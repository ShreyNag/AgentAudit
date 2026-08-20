"""Shared persistence of a finalized ``ExecutionTrace``'s artifacts.

Factored out of ``app.services.execution_service.ExecutionService`` (PROJECT_SPEC_1 SS97's
persist-trace-then-events-then-tool-calls sequence) so
``app.services.trace_ingestion_service.TraceIngestionService`` persists externally produced
traces through the exact same path -- one implementation, not two copies that could drift apart.
"""

from __future__ import annotations

from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.trace.models import ExecutionTrace


async def persist_trace_artifacts(
    *,
    trace_repository: TraceRepository,
    trace_event_repository: TraceEventRepository,
    tool_call_repository: ToolCallRepository,
    tool_output_repository: ToolOutputRepository,
    run_id: int,
    trace: ExecutionTrace,
) -> None:
    """Persist ``trace``'s document, its events, and its tool calls/outputs for ``run_id``.

    Callers are responsible for validating that ``trace.tool_calls``/``trace.tool_outputs`` are
    pairwise matched by index beforehand -- the right error to raise on a mismatch differs by
    caller (``ExecutionService`` can only get this from an internal bug; an ingested external
    trace can get it from a malformed submission), so it is not this function's concern.
    """
    await trace_repository.save_trace(
        run_id,
        trace_json=trace.model_dump(mode="json"),
        planner=trace.planner,
        reasoning=trace.reasoning,
        messages=trace.messages,
        trace_metadata=trace.metadata,
        statistics=trace.statistics,
        version=trace.version,
    )

    if trace.events:
        await trace_event_repository.bulk_create(
            [
                {
                    "run_id": run_id,
                    "event_number": event.sequence_number,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "component": event.component,
                    "payload": {
                        "input": event.input,
                        "output": event.output,
                        "error": event.error,
                    },
                    "latency": event.latency,
                    "status": event.status,
                }
                for event in trace.events
            ]
        )

    for order, (call, output) in enumerate(
        zip(trace.tool_calls, trace.tool_outputs, strict=True), start=1
    ):
        call_row = await tool_call_repository.create(
            run_id=run_id,
            tool_name=call["tool_name"],
            arguments=call["arguments"],
            validated_arguments=call["arguments"],
            execution_order=order,
            latency=call.get("latency"),
            status=call["status"],
            error=output.get("error"),
        )
        await tool_output_repository.create(
            tool_call_id=call_row.id,
            output=output.get("output", {}),
            correct=None,
            output_metadata={},
        )
