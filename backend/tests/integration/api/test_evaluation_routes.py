"""End-to-end API test: launch a run, then evaluate it and read back every evaluation endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import ProviderResponse, ToolCallSchema
from tests.unit.evaluation.conftest import FakeJudgeProvider
from tests.unit.execution.conftest import FakeSequentialProvider


class _StaticFakeAUT(FakeSequentialProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(
            config,
            [
                ProviderResponse(
                    provider=config.provider,
                    model=config.model,
                    tool_calls=[
                        ToolCallSchema(
                            id="tc-1",
                            tool_name="bank_transfer",
                            arguments={
                                "from_account": "acct-1",
                                "to_account": "acct-4",
                                "amount": 200.0,
                            },
                        )
                    ],
                ),
                ProviderResponse(
                    provider=config.provider, model=config.model, content="Transferred $200."
                ),
            ],
        )


class _StaticFakeJudge(FakeJudgeProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)


@pytest.fixture(autouse=True)
def _register_fakes_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("test-fake-aut", _StaticFakeAUT)
    ProviderFactory.register("test-fake-judge", _StaticFakeJudge)
    monkeypatch.setenv("AUT_PROVIDER", "test-fake-aut")
    monkeypatch.setenv("AUT_MODEL", "fake-model")
    monkeypatch.setenv("AUT_API_KEY", "x")
    monkeypatch.setenv("JUDGE_PROVIDER", "test-fake-judge")
    monkeypatch.setenv("JUDGE_MODEL", "fake-judge-model")
    monkeypatch.setenv("JUDGE_API_KEY", "x")


@pytest.mark.asyncio
class TestEvaluationEndpoints:
    async def test_launch_then_evaluate_full_round_trip(self, async_client: AsyncClient) -> None:
        # GET /benchmarks lazily seeds the environment/task tables (BenchmarkService.ensure_seeded)
        # -- /benchmarks/run itself never seeds, mirroring how the real frontend always lists
        # benchmarks before a user can launch one.
        await async_client.get("/api/v1/benchmarks")
        launch_response = await async_client.post(
            "/api/v1/benchmarks/run", json={"task_id": "banking-001"}
        )
        assert launch_response.status_code == 200
        run_id = launch_response.json()["data"]["id"]

        evaluate_response = await async_client.post(f"/api/v1/runs/{run_id}/evaluate")
        assert evaluate_response.status_code == 200
        assert evaluate_response.json()["data"]["cts_reported"] == pytest.approx(80.0)
        assert evaluate_response.json()["data"]["cts_raw"] == pytest.approx(80.0)
        assert evaluate_response.json()["data"]["critical_failure"] is False

        scores_response = await async_client.get(f"/api/v1/runs/{run_id}/evaluation")
        assert scores_response.status_code == 200
        assert len(scores_response.json()["data"]) == 10

        cts_response = await async_client.get(f"/api/v1/runs/{run_id}/cts")
        assert cts_response.status_code == 200
        assert cts_response.json()["data"]["trust_level"] == "High Trust"
        assert cts_response.json()["data"]["cts_raw"] == pytest.approx(80.0)
        assert cts_response.json()["data"]["cts_reported"] == pytest.approx(80.0)

        behaviour_response = await async_client.get(f"/api/v1/runs/{run_id}/behaviour")
        assert behaviour_response.status_code == 200
        assert behaviour_response.json()["data"]["classification"] == "SAFE_CORRECT"

    async def test_get_failure_before_evaluation_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.get("/api/v1/benchmarks")
        launch_response = await async_client.post(
            "/api/v1/benchmarks/run", json={"task_id": "banking-001"}
        )
        run_id = launch_response.json()["data"]["id"]
        response = await async_client.get(f"/api/v1/runs/{run_id}/failure")
        assert response.status_code == 404

    async def test_get_rubrics_returns_all_ten_evaluators(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/evaluators/rubrics")
        assert response.status_code == 200
        rubrics = response.json()["data"]
        assert len(rubrics) == 10
        assert set(rubrics["security"]["criteria"]) >= {"No unsafe tool execution"}
        assert [level["name"] for level in rubrics["security"]["levels"]] == [
            "Excellent",
            "Strong",
            "Acceptable",
            "Weak",
            "Critical Failure",
        ]
