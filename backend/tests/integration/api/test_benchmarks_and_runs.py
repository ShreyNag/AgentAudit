"""End-to-end API test: seed -> list benchmarks -> launch a run -> read back trace/timeline.

Exercises the full stack through HTTP, the same path a real client uses, per PROJECT_SPEC_2
SS124's end-to-end workflow (minus evaluation, which does not exist until Phase 9).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import ProviderResponse, ToolCallSchema
from tests.unit.execution.conftest import FakeSequentialProvider


class _StaticFakeProvider(FakeSequentialProvider):
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


@pytest.fixture(autouse=True)
def _register_fake_provider_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("test-fake", _StaticFakeProvider)
    monkeypatch.setenv("AUT_PROVIDER", "test-fake")
    monkeypatch.setenv("AUT_MODEL", "fake-model")
    monkeypatch.setenv("AUT_API_KEY", "x")


@pytest.mark.asyncio
class TestBenchmarkAndRunEndpoints:
    async def test_list_environments(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/environments")
        assert response.status_code == 200
        names = {env["name"] for env in response.json()["data"]}
        assert "banking" in names

    async def test_list_and_get_benchmark_task(self, async_client: AsyncClient) -> None:
        list_response = await async_client.get("/api/v1/benchmarks")
        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) >= 9  # 9 seed tasks across 8 environments

        get_response = await async_client.get("/api/v1/benchmarks/banking-001")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["task_id"] == "banking-001"

    async def test_get_unknown_benchmark_task_returns_404(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/benchmarks/does-not-exist")
        assert response.status_code == 404
        assert response.json()["status"] == "error"

    async def test_launch_run_then_read_trace_and_timeline(self, async_client: AsyncClient) -> None:
        # GET /benchmarks lazily seeds the environment/task tables (BenchmarkService.ensure_seeded)
        # -- /benchmarks/run itself never seeds, mirroring how the real frontend always lists
        # benchmarks before a user can launch one.
        await async_client.get("/api/v1/benchmarks")
        launch_response = await async_client.post(
            "/api/v1/benchmarks/run", json={"task_id": "banking-001"}
        )
        assert launch_response.status_code == 200
        run = launch_response.json()["data"]
        assert run["status"] == "completed"
        run_id = run["id"]

        get_run_response = await async_client.get(f"/api/v1/runs/{run_id}")
        assert get_run_response.status_code == 200

        trace_response = await async_client.get(f"/api/v1/runs/{run_id}/trace")
        assert trace_response.status_code == 200

        timeline_response = await async_client.get(f"/api/v1/runs/{run_id}/timeline")
        assert timeline_response.status_code == 200
        assert len(timeline_response.json()["data"]) > 0

        replay_response = await async_client.get(f"/api/v1/runs/{run_id}/replay")
        assert replay_response.status_code == 200
        assert replay_response.json()["data"]["final_response"] == "Transferred $200."

    async def test_list_runs_supports_pagination_metadata(self, async_client: AsyncClient) -> None:
        await async_client.post("/api/v1/benchmarks/run", json={"task_id": "banking-001"})
        response = await async_client.get("/api/v1/runs?page=1&page_size=10")
        assert response.status_code == 200
        assert "total_items" in response.json()["metadata"]

    async def test_delete_run_with_history_is_rejected(self, async_client: AsyncClient) -> None:
        await async_client.get("/api/v1/benchmarks")
        launch_response = await async_client.post(
            "/api/v1/benchmarks/run", json={"task_id": "banking-001"}
        )
        run_id = launch_response.json()["data"]["id"]
        delete_response = await async_client.delete(f"/api/v1/runs/{run_id}")
        assert delete_response.status_code == 400
