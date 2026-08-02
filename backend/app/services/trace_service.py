"""``TraceService`` (PROJECT_SPEC_2 SS87): read-only access to persisted execution traces.

Never performs evaluation (PROJECT_SPEC_2 SS87) and never invokes a provider -- replay
reconstructs entirely from persisted rows (PROJECT_SPEC_2 SS90/SS98).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.exceptions import NotFoundError
from app.models.execution_trace import ExecutionTraceModel
from app.models.trace_event import TraceEventModel
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.services.base import BaseService
from app.trace.models import ExecutionTrace
from app.trace.replay import ReplayLoader


class TraceService(BaseService):
    """Retrieves and replays persisted execution traces (exports live in ExportService)."""

    def __init__(
        self, trace_repository: TraceRepository, trace_event_repository: TraceEventRepository
    ) -> None:
        """Bind the service to the repositories backing traces and their timeline events."""
        self._trace_repository = trace_repository
        self._trace_event_repository = trace_event_repository

    async def get_trace(self, run_id: int) -> ExecutionTraceModel:
        """Return the persisted trace row for ``run_id``.

        Raises:
            NotFoundError: if no trace has been persisted for ``run_id``.
        """
        trace = await self._trace_repository.load_by_run(run_id)
        if trace is None:
            raise NotFoundError(f"No execution trace persisted for run_id {run_id}.")
        return trace

    async def get_timeline(self, run_id: int) -> Sequence[TraceEventModel]:
        """Return every trace event for ``run_id``, in chronological order."""
        return await self._trace_event_repository.list_by_run(run_id)

    async def replay(self, run_id: int) -> ExecutionTrace:
        """Reconstruct the in-memory :class:`~app.trace.models.ExecutionTrace` for ``run_id``.

        Never re-invokes the original LLM (PROJECT_SPEC_1 SS69).
        """
        loader = ReplayLoader(self._trace_repository, self._trace_event_repository)
        return await loader.load(run_id)
