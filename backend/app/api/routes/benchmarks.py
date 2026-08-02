"""Benchmark and environment endpoints (PROJECT_SPEC_2 SS94)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import BenchmarkServiceDep
from app.core.exceptions import NotFoundError
from app.schemas.benchmark import BenchmarkEnvironmentResponse, BenchmarkTaskResponse
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])
environments_router = APIRouter(prefix="/environments", tags=["environments"])


@router.get("", response_model=StandardResponse[list[BenchmarkTaskResponse]])
async def list_benchmark_tasks(
    service: BenchmarkServiceDep, environment: str | None = None
) -> StandardResponse[list[BenchmarkTaskResponse]]:
    """List persisted benchmark tasks, optionally filtered by environment."""
    await service.ensure_seeded()
    tasks = await service.list_tasks(environment=environment)
    return StandardResponse(data=[BenchmarkTaskResponse.model_validate(t) for t in tasks])


@router.get("/{task_id}", response_model=StandardResponse[BenchmarkTaskResponse])
async def get_benchmark_task(
    task_id: str, service: BenchmarkServiceDep
) -> StandardResponse[BenchmarkTaskResponse]:
    """Return one benchmark task by its external ``task_id``.

    Raises:
        NotFoundError: if no task is registered under ``task_id``.
    """
    await service.ensure_seeded()
    task = await service.get_task(task_id)
    if task is None:
        raise NotFoundError(f"No benchmark task registered under '{task_id}'.")
    return StandardResponse(data=BenchmarkTaskResponse.model_validate(task))


@environments_router.get("", response_model=StandardResponse[list[BenchmarkEnvironmentResponse]])
async def list_environments(
    service: BenchmarkServiceDep,
) -> StandardResponse[list[BenchmarkEnvironmentResponse]]:
    """List every registered benchmark environment and its toolset."""
    environments = service.list_registered_environments()
    return StandardResponse(
        data=[
            BenchmarkEnvironmentResponse(
                name=env.name,
                description=env.description,
                version=env.version,
                toolset=env.toolset,
                difficulty_levels=env.difficulty_levels,
            )
            for env in environments
        ]
    )
