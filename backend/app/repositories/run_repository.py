"""``RunRepository`` (PROJECT_SPEC_2 SS83-84)."""

from __future__ import annotations

from app.models.run import RunModel
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[RunModel]):
    """Persistence for :class:`~app.models.run.RunModel`."""

    model = RunModel

    async def get_by_uuid(self, run_uuid: str) -> RunModel | None:
        """Return the run identified by its externally-facing ``run_uuid``."""
        return await self.find_one(run_uuid=run_uuid)

    async def update_status(self, run_id: int, status: str) -> RunModel | None:
        """Transition a run to a new lifecycle status (PROJECT_SPEC_2 SS110)."""
        return await self.update(run_id, status=status)
