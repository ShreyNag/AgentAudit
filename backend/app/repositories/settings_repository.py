"""``SettingsRepository`` (PROJECT_SPEC_1 SS89). Secrets never live here (PROJECT_SPEC_1 SS101)."""

from __future__ import annotations

from typing import Any

from app.models.system_settings import SystemSettingsModel
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[SystemSettingsModel]):
    """Persistence for :class:`~app.models.system_settings.SystemSettingsModel`."""

    model = SystemSettingsModel

    async def get_by_key(self, key: str) -> SystemSettingsModel | None:
        """Return the setting registered under ``key``, or ``None``."""
        return await self.find_one(key=key)

    async def set_value(
        self, key: str, value: Any, description: str | None = None
    ) -> SystemSettingsModel:
        """Create or update the setting registered under ``key``."""
        existing = await self.get_by_key(key)
        if existing is None:
            return await self.create(key=key, value=value, description=description)
        existing.value = value
        if description is not None:
            existing.description = description
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
