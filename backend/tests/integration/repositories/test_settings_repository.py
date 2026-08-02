"""``SettingsRepository`` create-or-update semantics."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings_repository import SettingsRepository


@pytest.mark.asyncio
class TestSettingsRepository:
    async def test_set_value_creates_when_absent(self, db_session: AsyncSession) -> None:
        repo = SettingsRepository(db_session)
        setting = await repo.set_value("max_iterations", 10, description="Planner loop limit.")
        assert setting.value == 10

    async def test_set_value_updates_existing_key(self, db_session: AsyncSession) -> None:
        repo = SettingsRepository(db_session)
        await repo.set_value("max_iterations", 10)
        updated = await repo.set_value("max_iterations", 20)
        assert updated.value == 20
        assert await repo.count() == 1

    async def test_get_by_key_returns_none_when_missing(self, db_session: AsyncSession) -> None:
        repo = SettingsRepository(db_session)
        assert await repo.get_by_key("does-not-exist") is None
