"""``POST /runs/external``: ingest a trace for an independently running agent over HTTP, then
evaluate it through the existing, unmodified evaluation endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.trace.tracer import AgentAuditTracer
from tests.unit.evaluation.conftest import FakeJudgeProvider


class _ExternalTraceTestJudge(FakeJudgeProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)


@pytest.fixture(autouse=True)
def _register_fake_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("external-trace-fake-judge", _ExternalTraceTestJudge)
    monkeypatch.setenv("JUDGE_PROVIDER", "external-trace-fake-judge")
    monkeypatch.setenv("JUDGE_MODEL", "fake-judge-model")
    monkeypatch.setenv("JUDGE_API_KEY", "x")


def _build_external_trace() -> dict[str, object]:
    tracer = AgentAuditTracer.start_run(
        task_id="trip_planner-001",
        environment="trip_planner",
        agent_name="trip-planner-bot",
        agent_id="v1",
    )
    tracer.record_llm_call(model="mock-llm", input="plan the trip", output="Searching flights.")
    tracer.record_tool_call(
        tool_name="flight_search", input={"destination": "Mumbai"},
        output={"flights": [{"id": "fl-2", "price": 480.0}]},
    )
    tracer.record_tool_call(
        tool_name="book_flight", input={"flight_id": "fl-2"},
        output={"booking_id": "booking-1", "status": "booked"},
    )
    trace = tracer.finish(final_output="Booked flight fl-2.", status="success")
    return trace.model_dump(mode="json")


@pytest.mark.asyncio
class TestExternalTraceIngestionEndpoint:
    async def test_ingest_evaluate_and_retrieve_score(self, async_client: AsyncClient) -> None:
        # Benchmark tasks auto-seed the first time they're listed (same as test_full_lifecycle).
        await async_client.get("/api/v1/benchmarks")

        trace_payload = _build_external_trace()

        ingest = await async_client.post(
            "/api/v1/runs/external",
            json={
                "trace": trace_payload,
                "environment": "trip_planner",
                "provider": "external-mock-llm",
                "model": "mock-llm-1",
                "task_id": "trip_planner-001",
            },
        )
        assert ingest.status_code == 200
        run = ingest.json()["data"]
        assert run["status"] == "completed"
        assert run["provider"] == "external-mock-llm"
        assert run["execution_mode"] == "external"
        # Before evaluation, no Judge has run yet -- the Run Details page must show "-- / --".
        assert run["judge_provider"] is None
        assert run["judge_model"] is None
        run_id = run["id"]

        trace_response = await async_client.get(f"/api/v1/runs/{run_id}/trace")
        assert trace_response.status_code == 200
        assert trace_response.json()["data"]["metadata"]["agent_name"] == "trip-planner-bot"
        assert trace_response.json()["data"]["metadata"]["agent_id"] == "v1"
        assert trace_response.json()["data"]["metadata"]["source"] == "external_agent"

        lookup = await async_client.get(f"/api/v1/runs/external/{trace_payload['run_uuid']}")
        assert lookup.status_code == 200
        assert lookup.json()["data"]["id"] == run_id

        evaluate = await async_client.post(f"/api/v1/runs/{run_id}/evaluate")
        assert evaluate.status_code == 200
        assert evaluate.json()["data"]["cts"] is not None

        scores = await async_client.get(f"/api/v1/runs/{run_id}/evaluation")
        assert len(scores.json()["data"]) == 10

        # After evaluation, the Run Details API must return the Judge actually used -- read from
        # the currently configured Judge (this test's own fixture), never a hardcoded value: an
        # externally-ingested run never has a Judge set at ingestion time (TraceIngestionService
        # sets neither field), so this can only come from evaluate_run() recording it.
        run_after_eval = await async_client.get(f"/api/v1/runs/{run_id}")
        assert run_after_eval.json()["data"]["judge_provider"] == "external-trace-fake-judge"
        assert run_after_eval.json()["data"]["judge_model"] == "fake-judge-model"

        cts = await async_client.get(f"/api/v1/runs/{run_id}/cts")
        assert cts.status_code == 200
        assert cts.json()["data"]["trust_level"]

    async def test_ingest_is_idempotent_over_http(self, async_client: AsyncClient) -> None:
        await async_client.get("/api/v1/benchmarks")
        trace_payload = _build_external_trace()
        body = {
            "trace": trace_payload, "environment": "trip_planner",
            "provider": "external-mock-llm", "model": "mock-llm-1",
            "task_id": "trip_planner-001",
        }

        first = await async_client.post("/api/v1/runs/external", json=body)
        second = await async_client.post("/api/v1/runs/external", json=body)

        assert first.json()["data"]["id"] == second.json()["data"]["id"]

    async def test_ingest_without_a_known_task_id_still_succeeds(
        self, async_client: AsyncClient
    ) -> None:
        tracer = AgentAuditTracer.start_run(environment="custom_research_agent")
        tracer.record_llm_call(model="mock-llm", input="research X", output="Findings on X.")
        trace = tracer.finish(final_output="Findings on X.", status="success")

        ingest = await async_client.post(
            "/api/v1/runs/external",
            json={
                "trace": trace.model_dump(mode="json"),
                "environment": "custom_research_agent",
                "provider": "external",
                "model": "external",
                "task_instruction": "Research topic X and summarize findings.",
            },
        )
        assert ingest.status_code == 200
        run_id = ingest.json()["data"]["id"]

        evaluate = await async_client.post(f"/api/v1/runs/{run_id}/evaluate")
        assert evaluate.status_code == 200

    async def test_lookup_by_uuid_404s_while_no_trace_has_been_ingested_yet(
        self, async_client: AsyncClient
    ) -> None:
        """The expected "waiting for agent" state -- a run_id generated client-side before any
        agent has run yet must not resolve to anything (PROJECT_SPEC_1: AgentAudit never creates
        a run row it hasn't actually observed)."""
        response = await async_client.get("/api/v1/runs/external/not-a-real-run-uuid")
        assert response.status_code == 404
        assert response.json()["status"] == "error"

    async def test_existing_benchmark_run_endpoint_is_unaffected(
        self, async_client: AsyncClient
    ) -> None:
        """Adding the external-trace router must not change any existing route's behavior."""
        response = await async_client.get("/api/v1/runs")
        assert response.status_code == 200
