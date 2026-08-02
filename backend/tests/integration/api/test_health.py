"""Integration tests for the health endpoints (PROJECT_SPEC_2 SS21/SS93)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """The application starts successfully and reports health without leaking secrets."""

    async def test_liveness(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "application_version" in body["data"]

    async def test_liveness_sets_correlation_id_header(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers

    async def test_database_health_reports_reachable_on_sqlite_memory(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/health/database")
        assert response.status_code == 200
        assert response.json()["data"]["reachable"] is True

    async def test_providers_health_lists_supported_providers(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/health/providers")
        assert response.status_code == 200
        providers = response.json()["data"]["supported_providers"]
        assert "anthropic" in providers
        assert "openai" in providers

    async def test_system_health_never_returns_secret_key(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health/system")
        assert response.status_code == 200
        assert "secret_key" not in response.text.lower()
