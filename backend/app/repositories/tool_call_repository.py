"""``ToolCallRepository`` and ``ToolOutputRepository`` (PROJECT_SPEC_1 SS83-84)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.tool_call import ToolCallModel
from app.models.tool_output import ToolOutputModel
from app.repositories.base import BaseRepository


class ToolCallRepository(BaseRepository[ToolCallModel]):
    """Persistence for :class:`~app.models.tool_call.ToolCallModel`."""

    model = ToolCallModel

    async def list_by_run(self, run_id: int) -> Sequence[ToolCallModel]:
        """Return every tool call for ``run_id``, ordered by ``execution_order`` ascending."""
        stmt = (
            select(ToolCallModel)
            .where(ToolCallModel.run_id == run_id)
            .order_by(ToolCallModel.execution_order.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ToolOutputRepository(BaseRepository[ToolOutputModel]):
    """Persistence for :class:`~app.models.tool_output.ToolOutputModel`."""

    model = ToolOutputModel

    async def get_by_tool_call(self, tool_call_id: int) -> ToolOutputModel | None:
        """Return the output recorded for a specific tool call, if any."""
        return await self.find_one(tool_call_id=tool_call_id)
