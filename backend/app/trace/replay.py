"""``ReplayLoader`` (PROJECT_SPEC_1 SS69, PROJECT_SPEC_6 SS57): reconstruct without re-running.

Reconstructs an :class:`~app.trace.models.ExecutionTrace` entirely from persisted rows -- it
never invokes a provider or re-executes tools (PROJECT_SPEC_2 SS90/SS98).
"""

from __future__ import annotations

import uuid

from app.core.exceptions import TraceError
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.trace.events import TraceEventType
from app.trace.models import ExecutionTrace, TraceEvent


class ReplayLoader:
    """Loads a historical run's persisted trace back into an in-memory ``ExecutionTrace``."""

    def __init__(
        self, trace_repository: TraceRepository, trace_event_repository: TraceEventRepository
    ) -> None:
        """Bind the loader to the repositories it reads persisted trace data from."""
        self._trace_repository = trace_repository
        self._trace_event_repository = trace_event_repository

    async def load(self, run_id: int) -> ExecutionTrace:
        """Reconstruct the full :class:`ExecutionTrace` for ``run_id``.

        Raises:
            TraceError: if no execution trace has been persisted for ``run_id``.
        """
        trace_row = await self._trace_repository.load_by_run(run_id)
        if trace_row is None:
            raise TraceError(f"No execution trace persisted for run_id {run_id}.")

        event_rows = await self._trace_event_repository.list_by_run(run_id)
        events: list[TraceEvent] = []
        for row in event_rows:
            try:
                event_type = TraceEventType(row.event_type)
            except ValueError:
                event_type = TraceEventType.WARNING
            events.append(
                TraceEvent(
                    event_id=str(uuid.uuid4()),
                    execution_id=str(run_id),
                    timestamp=row.timestamp,
                    event_type=event_type,
                    component=row.component,
                    output=row.payload,
                    latency=row.latency,
                    status=row.status,
                    sequence_number=row.event_number,
                )
            )

        trace_json = trace_row.trace_json if isinstance(trace_row.trace_json, dict) else {}
        return ExecutionTrace(
            run_uuid=str(trace_row.run_id),
            metadata=trace_row.trace_metadata,
            planner=trace_row.planner,
            reasoning=trace_row.reasoning,
            messages=trace_row.messages,
            final_response=trace_json.get("final_response"),
            statistics=trace_row.statistics,
            events=events,
            version=trace_row.version,
        )
