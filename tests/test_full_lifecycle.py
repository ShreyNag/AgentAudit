"""The complete end-to-end workflow (PROJECT_SPEC_2 SS124):

    Launch Benchmark -> Execute AUT -> Persist Trace -> Run Evaluation -> Store Scores ->
    Retrieve Report -> Replay Trace -> Export Results

Exercised entirely through the public REST API, exactly as a real client would, with the AUT and
Judge both backed by deterministic fake providers so the scenario runs without real credentials
or network access.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import ProviderResponse, ToolCallSchema
from tests.unit.evaluation.conftest import FakeJudgeProvider
from tests.unit.execution.conftest import FakeSequentialProvider


class _FullLifecycleAUT(FakeSequentialProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(
            config,
            [
                ProviderResponse(
                    provider=config.provider,
                    model=config.model,
                    tool_calls=[
                        ToolCallSchema(
                            id="tc-1", tool_name="book_flight", arguments={"flight_id": "fl-2"}
                        )
                    ],
                ),
                ProviderResponse(
                    provider=config.provider, model=config.model, content="Booked flight fl-2."
                ),
            ],
        )


class _FullLifecycleJudge(FakeJudgeProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)


@pytest.fixture(autouse=True)
def _register_fake_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("e2e-fake-aut", _FullLifecycleAUT)
    ProviderFactory.register("e2e-fake-judge", _FullLifecycleJudge)
    monkeypatch.setenv("AUT_PROVIDER", "e2e-fake-aut")
    monkeypatch.setenv("AUT_MODEL", "fake-model")
    monkeypatch.setenv("AUT_API_KEY", "x")
    monkeypatch.setenv("JUDGE_PROVIDER", "e2e-fake-judge")
    monkeypatch.setenv("JUDGE_MODEL", "fake-judge-model")
    monkeypatch.setenv("JUDGE_API_KEY", "x")


@pytest.mark.asyncio
class TestFullLifecycle:
    async def test_launch_execute_evaluate_replay_export(self, async_client: AsyncClient) -> None:
        # 1. Discover the benchmark (auto-seeds on first request).
        benchmarks = await async_client.get("/api/v1/benchmarks")
        assert benchmarks.status_code == 200
        assert len(benchmarks.json()["data"]) >= 7

        # 2. Launch Benchmark -> Execute AUT -> Persist Trace.
        launch = await async_client.post("/api/v1/benchmarks/run", json={"task_id": "travel-001"})
        assert launch.status_code == 200
        run = launch.json()["data"]
        assert run["status"] == "completed"
        run_id = run["id"]

        trace = await async_client.get(f"/api/v1/runs/{run_id}/trace")
        assert trace.status_code == 200

        # 3. Run Evaluation -> Store Scores.
        evaluate = await async_client.post(f"/api/v1/runs/{run_id}/evaluate")
        assert evaluate.status_code == 200
        assert evaluate.json()["data"]["cts"] == pytest.approx(8.0)

        scores = await async_client.get(f"/api/v1/runs/{run_id}/evaluation")
        assert len(scores.json()["data"]) == 10

        # 4. Retrieve Report (CTS + behaviour).
        cts = await async_client.get(f"/api/v1/runs/{run_id}/cts")
        assert cts.json()["data"]["trust_level"] == "High Trust"
        behaviour = await async_client.get(f"/api/v1/runs/{run_id}/behaviour")
        assert behaviour.json()["data"]["classification"] == "SAFE_CORRECT"

        # 5. Replay Trace -- reconstructed from persisted rows, no LLM involved.
        replay = await async_client.get(f"/api/v1/runs/{run_id}/replay")
        assert replay.status_code == 200
        assert replay.json()["data"]["final_response"] == "Booked flight fl-2."

        # 6. Export Results in every supported format.
        export_json = await async_client.get(f"/api/v1/runs/{run_id}/export/json")
        assert export_json.status_code == 200
        export_markdown = await async_client.get(f"/api/v1/runs/{run_id}/export/markdown")
        assert "Composite Trust Score" in export_markdown.text
        export_csv = await async_client.get(f"/api/v1/runs/{run_id}/export/csv")
        assert "security" in export_csv.text

        # 7. Dashboard reflects the completed, evaluated run.
        summary = await async_client.get("/api/v1/dashboard/summary")
        assert summary.json()["data"]["total_runs"] == 1
        assert summary.json()["data"]["average_cts"] == pytest.approx(8.0)
