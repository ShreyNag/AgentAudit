"""Export endpoint tests (PROJECT_SPEC_2 SS100): JSON, Markdown, CSV."""

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
def _register_fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderFactory.register("test-fake", _StaticFakeProvider)
    monkeypatch.setenv("AUT_PROVIDER", "test-fake")
    monkeypatch.setenv("AUT_MODEL", "fake-model")
    monkeypatch.setenv("AUT_API_KEY", "x")


@pytest.mark.asyncio
class TestExportEndpoints:
    async def test_export_json_matches_the_trace(self, async_client: AsyncClient) -> None:
        await async_client.get("/api/v1/benchmarks")
        launch = await async_client.post("/api/v1/benchmarks/run", json={"task_id": "banking-001"})
        run_id = launch.json()["data"]["id"]

        response = await async_client.get(f"/api/v1/runs/{run_id}/export/json")
        assert response.status_code == 200
        assert response.json()["data"]["final_response"] == "Transferred $200."

    async def test_export_markdown_contains_run_summary(self, async_client: AsyncClient) -> None:
        await async_client.get("/api/v1/benchmarks")
        launch = await async_client.post("/api/v1/benchmarks/run", json={"task_id": "banking-001"})
        run_id = launch.json()["data"]["id"]

        response = await async_client.get(f"/api/v1/runs/{run_id}/export/markdown")
        assert response.status_code == 200
        assert "# AgentAudit Report" in response.text
        assert "Transferred $200." in response.text

    async def test_export_csv_has_a_header_even_with_no_evaluation(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.get("/api/v1/benchmarks")
        launch = await async_client.post("/api/v1/benchmarks/run", json={"task_id": "banking-001"})
        run_id = launch.json()["data"]["id"]

        response = await async_client.get(f"/api/v1/runs/{run_id}/export/csv")
        assert response.status_code == 200
        assert response.text.strip() == "evaluator_name,score,confidence,rubric_level"
