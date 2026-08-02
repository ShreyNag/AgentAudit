"""Trace endpoints (PROJECT_SPEC_2 SS96/SS98): read-only execution data, no evaluation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import TraceServiceDep
from app.schemas.common import StandardResponse
from app.schemas.trace import TraceEventResponse, TraceResponse

router = APIRouter(prefix="/runs", tags=["traces"])


@router.get("/{run_id}/trace", response_model=StandardResponse[TraceResponse])
async def get_trace(run_id: int, service: TraceServiceDep) -> StandardResponse[TraceResponse]:
    """Return the persisted execution trace document for ``run_id``."""
    trace = await service.get_trace(run_id)
    return StandardResponse(data=TraceResponse.model_validate(trace))


@router.get("/{run_id}/events", response_model=StandardResponse[list[TraceEventResponse]])
async def get_trace_events(
    run_id: int, service: TraceServiceDep
) -> StandardResponse[list[TraceEventResponse]]:
    """Return every trace event for ``run_id``, ordered chronologically."""
    events = await service.get_timeline(run_id)
    return StandardResponse(data=[TraceEventResponse.model_validate(e) for e in events])


@router.get("/{run_id}/timeline", response_model=StandardResponse[list[TraceEventResponse]])
async def get_trace_timeline(
    run_id: int, service: TraceServiceDep
) -> StandardResponse[list[TraceEventResponse]]:
    """Alias of :func:`get_trace_events`, powering the frontend execution timeline."""
    return await get_trace_events(run_id, service)


@router.get("/{run_id}/messages", response_model=StandardResponse[list[dict[str, object]]])
async def get_trace_messages(
    run_id: int, service: TraceServiceDep
) -> StandardResponse[list[dict[str, object]]]:
    """Return the immutable conversation history recorded for ``run_id``."""
    trace = await service.get_trace(run_id)
    return StandardResponse(data=list(trace.messages))


@router.get("/{run_id}/replay", response_model=StandardResponse[dict[str, object]])
async def replay_run(run_id: int, service: TraceServiceDep) -> StandardResponse[dict[str, object]]:
    """Reconstruct the full execution trace for ``run_id`` without invoking any LLM."""
    trace = await service.replay(run_id)
    return StandardResponse(data=trace.model_dump(mode="json"))


# JSON/Markdown/CSV exports live in app.api.routes.exports (PROJECT_SPEC_2 SS100), backed by
# ExportService rather than TraceService, so every export format shares one implementation.
