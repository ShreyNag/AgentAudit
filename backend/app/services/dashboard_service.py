"""``DashboardService`` (PROJECT_SPEC_2 SS89, PROJECT_SPEC_1 SS22): read-only aggregation.

The frontend dashboard reaches this data only through the REST API this service backs -- never
by querying repositories directly.
"""

from __future__ import annotations

from app.repositories.evaluation_repository import (
    EvaluationReportRepository,
    EvaluationScoreRepository,
)
from app.repositories.run_repository import RunRepository
from app.services.base import BaseService


class DashboardService(BaseService):
    """Aggregates run, provider, environment, and evaluator statistics for the dashboard."""

    def __init__(
        self,
        run_repository: RunRepository,
        evaluation_report_repository: EvaluationReportRepository,
        evaluation_score_repository: EvaluationScoreRepository,
    ) -> None:
        """Bind the service to the repositories it aggregates statistics from."""
        self._run_repository = run_repository
        self._evaluation_report_repository = evaluation_report_repository
        self._evaluation_score_repository = evaluation_score_repository

    async def summary(self) -> dict[str, object]:
        """Return top-line dashboard statistics (PROJECT_SPEC_4's Dashboard page)."""
        total_runs = await self._run_repository.count()
        completed_runs = await self._run_repository.count(status="completed")
        failed_runs = await self._run_repository.count(status="failed")
        running_runs = await self._run_repository.count(status="running")
        average_cts = await self._evaluation_report_repository.average_cts()
        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "average_cts": average_cts,
        }

    async def provider_breakdown(self) -> list[dict[str, object]]:
        """Return run counts grouped by provider, for provider comparison."""
        return await self._run_repository.count_grouped_by("provider")

    async def environment_breakdown(self) -> list[dict[str, object]]:
        """Return run counts grouped by benchmark environment."""
        return await self._run_repository.count_grouped_by("environment")

    async def execution_mode_breakdown(self) -> list[dict[str, object]]:
        """Return run counts grouped by execution mode ("benchmark" vs "external"; see
        ``app.core.constants.EXECUTION_MODES``)."""
        return await self._run_repository.count_grouped_by("execution_mode")

    async def evaluator_statistics(self) -> list[dict[str, object]]:
        """Return average score/confidence per evaluator, across every evaluated run."""
        return await self._evaluation_score_repository.average_by_evaluator()
