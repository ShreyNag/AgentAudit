"""``ProviderService`` (PROJECT_SPEC_2 SS17/SS89): provider discovery, health, and metadata."""

from __future__ import annotations

from app.config import Settings
from app.providers.factory import ProviderFactory
from app.providers.schemas import HealthCheckResult, ModelInfo
from app.repositories.provider_repository import ProviderRepository
from app.services.base import BaseService


class ProviderService(BaseService):
    """Exposes provider registry metadata and live AUT/Judge health checks."""

    def __init__(self, provider_repository: ProviderRepository) -> None:
        """Bind the service to the repository backing the ``providers`` table."""
        self._provider_repository = provider_repository

    def supported_providers(self) -> list[str]:
        """Return every provider name registered on :class:`ProviderFactory`."""
        return ProviderFactory.supported_providers()

    async def ensure_registered(self, provider_name: str, provider_type: str = "llm") -> None:
        """Upsert ``provider_name`` into the ``providers`` table (idempotent)."""
        existing = await self._provider_repository.get_by_name(provider_name)
        if existing is None:
            await self._provider_repository.create(
                provider_name=provider_name, provider_type=provider_type, enabled=True
            )

    async def check_aut_health(self, settings: Settings) -> HealthCheckResult:
        """Run a live health check against the configured AUT provider."""
        provider = await ProviderFactory.create_aut(settings)
        try:
            return await provider.health_check()
        finally:
            await provider.shutdown()

    async def check_judge_health(self, settings: Settings) -> HealthCheckResult:
        """Run a live health check against the configured Judge provider."""
        provider = await ProviderFactory.create_judge(settings)
        try:
            return await provider.health_check()
        finally:
            await provider.shutdown()

    async def list_aut_models(self, settings: Settings) -> list[ModelInfo]:
        """List models available through the configured AUT provider."""
        provider = await ProviderFactory.create_aut(settings)
        try:
            return await provider.list_models()
        finally:
            await provider.shutdown()
