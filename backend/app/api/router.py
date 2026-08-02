"""Aggregate ``/api/v1`` router.

Individual route modules register themselves here as they are implemented, so
:mod:`app.main` only ever needs to import a single router (PROJECT_SPEC_2 SS13).
"""

from fastapi import APIRouter

from app.api.routes import (
    benchmarks,
    dashboard,
    evaluation,
    exports,
    health,
    providers,
    runs,
    settings,
    traces,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(benchmarks.router)
api_router.include_router(benchmarks.environments_router)
api_router.include_router(runs.router)
api_router.include_router(runs.benchmark_run_router)
api_router.include_router(traces.router)
api_router.include_router(evaluation.router)
api_router.include_router(evaluation.rubric_router)
api_router.include_router(exports.router)
api_router.include_router(providers.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
