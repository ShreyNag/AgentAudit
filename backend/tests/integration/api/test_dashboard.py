"""Dashboard endpoint smoke tests (PROJECT_SPEC_2 SS99)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDashboardEndpoints:
    async def test_summary_returns_zeroed_counts_on_an_empty_database(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        assert response.json()["data"]["total_runs"] == 0

    async def test_root_dashboard_alias_matches_summary(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/dashboard")
        assert response.status_code == 200
        assert "total_runs" in response.json()["data"]

    async def test_providers_and_environments_breakdowns_are_empty_lists_initially(
        self, async_client: AsyncClient
    ) -> None:
        providers_response = await async_client.get("/api/v1/dashboard/providers")
        environments_response = await async_client.get("/api/v1/dashboard/environments")
        assert providers_response.json()["data"] == []
        assert environments_response.json()["data"] == []
