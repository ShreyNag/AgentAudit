"""Settings endpoint tests (PROJECT_SPEC_2 SS102)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSettingsEndpoints:
    async def test_list_settings_starts_empty(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/settings")
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_put_creates_then_lists_a_setting(self, async_client: AsyncClient) -> None:
        put_response = await async_client.put(
            "/api/v1/settings",
            json={"key": "max_iterations", "value": 10, "description": "Planner loop limit."},
        )
        assert put_response.status_code == 200
        assert put_response.json()["data"]["value"] == 10

        list_response = await async_client.get("/api/v1/settings")
        assert len(list_response.json()["data"]) == 1

    async def test_put_updates_an_existing_key_in_place(self, async_client: AsyncClient) -> None:
        await async_client.put("/api/v1/settings", json={"key": "max_iterations", "value": 10})
        response = await async_client.put(
            "/api/v1/settings", json={"key": "max_iterations", "value": 20}
        )
        assert response.json()["data"]["value"] == 20

        list_response = await async_client.get("/api/v1/settings")
        assert len(list_response.json()["data"]) == 1

    async def test_response_never_contains_a_secret_looking_field(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.put("/api/v1/settings", json={"key": "theme", "value": "dark"})
        response = await async_client.get("/api/v1/settings")
        assert "api_key" not in response.text.lower()
        assert "secret" not in response.text.lower()
