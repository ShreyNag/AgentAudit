"""Dashboard endpoints (PROJECT_SPEC_2 SS99)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.database import DbSession
from app.repositories.evaluation_repository import (
    EvaluationReportRepository,
    EvaluationScoreRepository,
)
from app.repositories.run_repository import RunRepository
from app.schemas.common import StandardResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    EvaluatorStatisticResponse,
    GroupedCountResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(session: DbSession) -> DashboardService:
    """Build a :class:`DashboardService` bound to the current request's session."""
    return DashboardService(
        RunRepository(session),
        EvaluationReportRepository(session),
        EvaluationScoreRepository(session),
    )


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get("", response_model=StandardResponse[DashboardSummaryResponse])
@router.get("/summary", response_model=StandardResponse[DashboardSummaryResponse])
async def get_dashboard_summary(
    service: DashboardServiceDep,
) -> StandardResponse[DashboardSummaryResponse]:
    """Return top-line dashboard statistics."""
    summary = await service.summary()
    return StandardResponse(data=DashboardSummaryResponse(**summary))


@router.get("/providers", response_model=StandardResponse[list[GroupedCountResponse]])
async def get_provider_breakdown(
    service: DashboardServiceDep,
) -> StandardResponse[list[GroupedCountResponse]]:
    """Return run counts grouped by provider."""
    breakdown = await service.provider_breakdown()
    return StandardResponse(
        data=[
            GroupedCountResponse(label=str(item["provider"]), count=item["count"])
            for item in breakdown
        ]
    )


@router.get("/environments", response_model=StandardResponse[list[GroupedCountResponse]])
async def get_environment_breakdown(
    service: DashboardServiceDep,
) -> StandardResponse[list[GroupedCountResponse]]:
    """Return run counts grouped by benchmark environment."""
    breakdown = await service.environment_breakdown()
    return StandardResponse(
        data=[
            GroupedCountResponse(label=str(item["environment"]), count=item["count"])
            for item in breakdown
        ]
    )


@router.get("/statistics", response_model=StandardResponse[list[EvaluatorStatisticResponse]])
async def get_evaluator_statistics(
    service: DashboardServiceDep,
) -> StandardResponse[list[EvaluatorStatisticResponse]]:
    """Return average score/confidence per evaluator, across every evaluated run."""
    statistics = await service.evaluator_statistics()
    return StandardResponse(data=[EvaluatorStatisticResponse(**item) for item in statistics])
