"""``ProviderRepository`` (PROJECT_SPEC_1 SS79)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.provider import ProviderModel
from app.repositories.base import BaseRepository


class ProviderRepository(BaseRepository[ProviderModel]):
    """Persistence for :class:`~app.models.provider.ProviderModel`."""

    model = ProviderModel

    async def get_by_name(self, provider_name: str) -> ProviderModel | None:
        """Return the provider registration with the given ``provider_name``, or ``None``."""
        return await self.find_one(provider_name=provider_name)

    async def list_enabled(self) -> Sequence[ProviderModel]:
        """Return every provider currently marked ``enabled``."""
        stmt = select(ProviderModel).where(ProviderModel.enabled.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()
