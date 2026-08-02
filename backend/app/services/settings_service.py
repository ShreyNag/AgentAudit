"""``SettingsService`` (PROJECT_SPEC_2 SS17/SS102).

Secrets are never returned here by construction, not by runtime filtering: the
``system_settings`` table is documented to hold only non-secret application configuration
(PROJECT_SPEC_1 SS89/SS101) -- API keys and passwords live exclusively in environment variables.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.models.system_settings import SystemSettingsModel
from app.repositories.settings_repository import SettingsRepository
from app.services.base import BaseService


class SettingsService(BaseService):
    """Reads and writes non-secret runtime configuration."""

    def __init__(self, settings_repository: SettingsRepository) -> None:
        """Bind the service to the repository backing the ``system_settings`` table."""
        self._settings_repository = settings_repository

    async def list_all(self) -> Sequence[SystemSettingsModel]:
        """Return every persisted setting."""
        return await self._settings_repository.list(page=1, page_size=500)

    async def get(self, key: str) -> SystemSettingsModel | None:
        """Return the setting registered under ``key``, or ``None``."""
        return await self._settings_repository.get_by_key(key)

    async def set(
        self, key: str, value: Any, description: str | None = None
    ) -> SystemSettingsModel:
        """Create or update the setting registered under ``key``."""
        return await self._settings_repository.set_value(key, value, description)
