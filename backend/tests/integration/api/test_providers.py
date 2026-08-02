"""Provider endpoint tests that do not require live/configured provider credentials."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProviderEndpoints:
    async def test_list_providers_returns_the_registered_names(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/providers")
        assert response.status_code == 200
        names = response.json()["data"]
        assert "anthropic" in names
        assert "openai" in names
