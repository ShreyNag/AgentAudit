"""Generic BaseRepository behavior, exercised against ProviderModel."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.provider_repository import ProviderRepository


@pytest.mark.asyncio
class TestBaseRepositoryCrud:
    async def test_create_and_get(self, db_session: AsyncSession) -> None:
        repo = ProviderRepository(db_session)
        created = await repo.create(provider_name="anthropic", provider_type="llm")
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.provider_name == "anthropic"

    async def test_list_applies_filters_and_pagination(self, db_session: AsyncSession) -> None:
        repo = ProviderRepository(db_session)
        for name in ("openai", "anthropic", "gemini"):
            await repo.create(provider_name=name, provider_type="llm", enabled=True)
        await repo.create(provider_name="disabled-one", provider_type="llm", enabled=False)

        enabled_only = await repo.list(page=1, page_size=2, enabled=True)
        assert len(enabled_only) == 2

        total_enabled = await repo.count(enabled=True)
        assert total_enabled == 3

    async def test_update_mutates_and_returns_instance(self, db_session: AsyncSession) -> None:
        repo = ProviderRepository(db_session)
        created = await repo.create(provider_name="groq", provider_type="llm", enabled=True)
        updated = await repo.update(created.id, enabled=False)
        assert updated is not None
        assert updated.enabled is False

    async def test_delete_removes_row(self, db_session: AsyncSession) -> None:
        repo = ProviderRepository(db_session)
        created = await repo.create(provider_name="ollama", provider_type="llm")
        deleted = await repo.delete(created.id)
        assert deleted is True
        assert await repo.get(created.id) is None

    async def test_exists_reflects_filter_match(self, db_session: AsyncSession) -> None:
        repo = ProviderRepository(db_session)
        assert await repo.exists(provider_name="deepseek") is False
        await repo.create(provider_name="deepseek", provider_type="llm")
        assert await repo.exists(provider_name="deepseek") is True
