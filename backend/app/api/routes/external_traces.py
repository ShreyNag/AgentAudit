"""External-trace ingestion endpoint: runs AgentAudit observed rather than executed itself.

Follows the same ``/runs`` prefix and ``StandardResponse`` envelope as every other run endpoint
(``app/api/routes/runs.py``, ``traces.py``) rather than introducing a new convention.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import RunRepositoryDep, TraceIngestionServiceDep
from app.core.exceptions import NotFoundError
from app.schemas.common import StandardResponse
from app.schemas.external_trace import ExternalRunIngestRequest
from app.schemas.run import RunResponse

router = APIRouter(prefix="/runs", tags=["external-traces"])


@router.post("/external", response_model=StandardResponse[RunResponse])
async def ingest_external_run(
    request: ExternalRunIngestRequest, service: TraceIngestionServiceDep
) -> StandardResponse[RunResponse]:
    """Persist a trace produced by ``AgentAuditTracer`` for an independently running agent as a
    new run, ready for the existing ``POST /runs/{run_id}/evaluate`` endpoint -- exactly like a
    run AgentAudit executed itself.

    Idempotent: re-submitting the same ``trace.run_uuid`` returns the already-persisted run
    rather than creating a duplicate.

    Raises:
        ValidationError: if the trace's tool calls and tool outputs are not pairwise matched.
    """
    run_row = await service.ingest(
        trace=request.trace,
        environment=request.environment,
        provider=request.provider,
        model=request.model,
        task_id=request.task_id,
        status=request.status,
        task_instruction=request.task_instruction,
        ground_truth=request.ground_truth,
    )
    return StandardResponse(
        message="External trace ingested.", data=RunResponse.model_validate(run_row)
    )


@router.get("/external/{run_uuid}", response_model=StandardResponse[RunResponse])
async def get_external_run_by_uuid(
    run_uuid: str, run_repository: RunRepositoryDep
) -> StandardResponse[RunResponse]:
    """Look up a run by the ``run_uuid`` an external agent's tracer was started with.

    Lets a client that generated a ``run_id`` *before* its agent ran (e.g. the frontend's
    "Create External Run" panel, which shows integration instructions before any trace exists)
    poll for whether that trace has been ingested yet -- AgentAudit never creates a run row for
    an external agent until it actually observes something (PROJECT_SPEC_1 SS106: execution and
    evaluation only ever follow a real persisted trace, never a promise of one).

    Raises:
        NotFoundError: if no run has been ingested yet under this ``run_uuid`` -- the expected,
            normal state while still waiting for the agent, not necessarily an error condition.
    """
    run = await run_repository.get_by_uuid(run_uuid)
    if run is None:
        raise NotFoundError(
            f"No trace has been ingested yet for run_uuid '{run_uuid}'. Still waiting for the "
            "external agent to submit its trace."
        )
    return StandardResponse(data=RunResponse.model_validate(run))
