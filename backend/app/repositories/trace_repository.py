"""``TraceRepository`` (PROJECT_SPEC_2 SS83-84): the persisted execution trace document."""

from __future__ import annotations

from typing import Any

from app.models.execution_trace import ExecutionTraceModel
from app.repositories.base import BaseRepository


class TraceRepository(BaseRepository[ExecutionTraceModel]):
    """Persistence for :class:`~app.models.execution_trace.ExecutionTraceModel`."""

    model = ExecutionTraceModel

    async def save_trace(self, run_id: int, **fields: Any) -> ExecutionTraceModel:
        """Persist a newly finalized execution trace for ``run_id``."""
        return await self.create(run_id=run_id, **fields)

    async def load_by_run(self, run_id: int) -> ExecutionTraceModel | None:
        """Load the execution trace for ``run_id``, or ``None`` if not yet persisted."""
        return await self.find_one(run_id=run_id)

    async def exists_for_run(self, run_id: int) -> bool:
        """Return whether a trace has already been persisted for ``run_id``."""
        return await self.exists(run_id=run_id)
