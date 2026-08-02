"""``TraceEventRepository`` (PROJECT_SPEC_2 SS83-84): ordered timeline events."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.models.trace_event import TraceEventModel
from app.repositories.base import BaseRepository


class TraceEventRepository(BaseRepository[TraceEventModel]):
    """Persistence for :class:`~app.models.trace_event.TraceEventModel`.

    Events must never be reordered once persisted (PROJECT_SPEC_2 SS79); this repository only
    ever appends new rows and reads them back in ``event_number`` order.
    """

    model = TraceEventModel

    async def bulk_create(self, events: Sequence[dict[str, Any]]) -> list[TraceEventModel]:
        """Insert many trace events in a single flush, preserving the given order."""
        instances = [TraceEventModel(**event) for event in events]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def list_by_run(self, run_id: int) -> Sequence[TraceEventModel]:
        """Return every event for ``run_id``, strictly ordered by ``event_number`` ascending."""
        stmt = (
            select(TraceEventModel)
            .where(TraceEventModel.run_id == run_id)
            .order_by(TraceEventModel.event_number.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
