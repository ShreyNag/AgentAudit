"""End-to-end proof of the external-agent tracing capability, using the actual example agent.

Runs the fully independent agent in ``examples/external_agent/independent_agent.py`` (its own
loop, its own mock LLM, its own tools -- no dependency on ``app.execution``), persists its trace
through the exact same session/database the running FastAPI app uses, then drives evaluation and
score retrieval entirely through the public REST API, exactly like ``test_full_lifecycle.py``
does for an AgentAudit-executed run. This is the comparison point: same benchmark task
(``trip_planner-001``), same evaluators, same endpoints, two different execution origins.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.providers.config import ProviderConfig  # noqa: E402
from app.providers.factory import ProviderFactory  # noqa: E402
from tests.unit.evaluation.conftest import FakeJudgeProvider  # noqa: E402


class _ExampleTestJudge(FakeJudgeProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)


@pytest.fixture(autouse=True)
def _register_fake_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("external-agent-example-judge", _ExampleTestJudge)
    monkeypatch.setenv("JUDGE_PROVIDER", "external-agent-example-judge")
    monkeypatch.setenv("JUDGE_MODEL", "fake-judge-model")
    monkeypatch.setenv("JUDGE_API_KEY", "x")


@pytest.mark.asyncio
class TestExternalAgentExampleLifecycle:
    async def test_independent_agent_trace_is_evaluable_through_the_public_api(
        self, async_client: AsyncClient
    ) -> None:
        from examples.external_agent.independent_agent import run_and_ingest

        # Auto-seeds trip_planner-001 (and every other benchmark task) on first request, exactly
        # as an AgentAudit-executed run of the same task would rely on.
        benchmarks = await async_client.get("/api/v1/benchmarks")
        assert benchmarks.status_code == 200

        from app.database.session import get_database

        database = get_database()
        session = database.session()
        try:
            run_row = await run_and_ingest(session)
            await session.commit()
        finally:
            await session.close()

        assert run_row.status == "completed"

        trace = await async_client.get(f"/api/v1/runs/{run_row.id}/trace")
        assert trace.status_code == 200

        evaluate = await async_client.post(f"/api/v1/runs/{run_row.id}/evaluate")
        assert evaluate.status_code == 200
        assert evaluate.json()["data"]["cts_reported"] is not None
        assert evaluate.json()["data"]["cts_raw"] is not None

        scores = await async_client.get(f"/api/v1/runs/{run_row.id}/evaluation")
        assert len(scores.json()["data"]) == 10

        behaviour = await async_client.get(f"/api/v1/runs/{run_row.id}/behaviour")
        assert behaviour.status_code == 200
        assert behaviour.json()["data"]["classification"]
