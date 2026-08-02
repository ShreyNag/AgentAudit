"""Run endpoints (PROJECT_SPEC_2 SS94-95): launching and querying benchmark executions."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import ExecutionServiceDep, RunRepositoryDep
from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.common import PaginatedMetadata, StandardResponse
from app.schemas.run import RunLaunchRequest, RunResponse

router = APIRouter(prefix="/runs", tags=["runs"])
benchmark_run_router = APIRouter(prefix="/benchmarks", tags=["runs"])


@benchmark_run_router.post("/run", response_model=StandardResponse[RunResponse])
async def launch_benchmark_run(
    request: RunLaunchRequest, service: ExecutionServiceDep
) -> StandardResponse[RunResponse]:
    """Launch a benchmark execution for ``request.task_id`` and return the persisted run.

    This call blocks until execution completes; PROJECT_SPEC_2 SS109's background-job model is
    the natural next step for long-running executions but is out of scope for this build.
    """
    settings = get_settings()
    run_row, _result = await service.launch(
        task_id=request.task_id,
        settings=settings,
        provider_name=request.provider,
        model=request.model,
    )
    return StandardResponse(
        message="Execution completed.", data=RunResponse.model_validate(run_row)
    )


@router.get("", response_model=StandardResponse[list[RunResponse]])
async def list_runs(
    run_repository: RunRepositoryDep,
    status: str | None = None,
    provider: str | None = None,
    environment: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> StandardResponse[list[RunResponse]]:
    """List runs with optional filtering, sorting, and pagination (PROJECT_SPEC_2 SS95/SS103)."""
    runs = await run_repository.list(
        page=page, page_size=page_size, status=status, provider=provider, environment=environment
    )
    total = await run_repository.count(status=status, provider=provider, environment=environment)
    return StandardResponse(
        data=[RunResponse.model_validate(run) for run in runs],
        metadata=PaginatedMetadata(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=max(1, -(-total // page_size)),
        ).model_dump(),
    )


@router.get("/{run_id}", response_model=StandardResponse[RunResponse])
async def get_run(run_id: int, run_repository: RunRepositoryDep) -> StandardResponse[RunResponse]:
    """Return one run by its internal ``id``.

    Raises:
        NotFoundError: if no run exists with the given ``run_id``.
    """
    run = await run_repository.get(run_id)
    if run is None:
        raise NotFoundError(f"No run with id {run_id}.")
    return StandardResponse(data=RunResponse.model_validate(run))


@router.get("/{run_id}/status", response_model=StandardResponse[dict[str, str]])
async def get_run_status(
    run_id: int, run_repository: RunRepositoryDep
) -> StandardResponse[dict[str, str]]:
    """Return only the current lifecycle status of a run."""
    run = await run_repository.get(run_id)
    if run is None:
        raise NotFoundError(f"No run with id {run_id}.")
    return StandardResponse(data={"status": run.status})


@router.delete("/{run_id}", response_model=StandardResponse[dict[str, bool]])
async def delete_run(
    run_id: int, run_repository: RunRepositoryDep
) -> StandardResponse[dict[str, bool]]:
    """Delete a run.

    Runs with persisted execution history (trace, events, tool calls) cannot be deleted -- the
    ``RESTRICT`` foreign keys on those tables enforce PROJECT_SPEC_1 SS91's "historical runs
    must remain immutable" requirement at the database level. This only succeeds for runs that
    never made it past initial persistence (e.g. failed before a trace was recorded).

    Raises:
        NotFoundError: if no run exists with the given ``run_id``.
        ValidationError: if the run still has referencing execution history.
    """
    try:
        deleted = await run_repository.delete(run_id)
    except IntegrityError as exc:
        raise ValidationError(
            "Cannot delete a run that still has persisted execution history."
        ) from exc
    if not deleted:
        raise NotFoundError(f"No run with id {run_id}.")
    return StandardResponse(data={"deleted": True})
