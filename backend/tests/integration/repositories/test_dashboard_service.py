"""``DashboardService`` aggregation (PROJECT_SPEC_2 SS89)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.evaluation_repository import (
    EvaluationReportRepository,
    EvaluationScoreRepository,
)
from app.repositories.run_repository import RunRepository
from app.services.dashboard_service import DashboardService


async def _make_run(
    db_session: AsyncSession, *, provider: str, environment: str, status: str
) -> int:
    task = await BenchmarkTaskRepository(db_session).create(
        task_id=f"{environment}-{uuid.uuid4().hex[:6]}",
        title="t",
        description="d",
        environment=environment,
        difficulty="easy",
        instruction="do it",
        ground_truth={"x": 1},
        expected_tool_sequence=[],
        task_metadata={},
    )
    run = await RunRepository(db_session).create(
        run_uuid=str(uuid.uuid4()),
        benchmark_task_id=task.id,
        provider=provider,
        model="m",
        environment=environment,
        status=status,
    )
    return run.id


@pytest.mark.asyncio
class TestDashboardService:
    async def test_summary_counts_runs_by_status(self, db_session: AsyncSession) -> None:
        await _make_run(db_session, provider="anthropic", environment="travel", status="completed")
        await _make_run(db_session, provider="openai", environment="email", status="failed")
        await _make_run(db_session, provider="anthropic", environment="travel", status="running")

        service = DashboardService(
            RunRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
        )
        summary = await service.summary()
        assert summary["total_runs"] == 3
        assert summary["completed_runs"] == 1
        assert summary["failed_runs"] == 1
        assert summary["running_runs"] == 1
        assert summary["average_cts_raw"] is None  # no evaluation reports yet

    async def test_provider_and_environment_breakdowns_group_correctly(
        self, db_session: AsyncSession
    ) -> None:
        await _make_run(db_session, provider="anthropic", environment="travel", status="completed")
        await _make_run(db_session, provider="anthropic", environment="banking", status="completed")
        await _make_run(db_session, provider="openai", environment="travel", status="completed")

        service = DashboardService(
            RunRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
        )
        providers = {row["provider"]: row["count"] for row in await service.provider_breakdown()}
        environments = {
            row["environment"]: row["count"] for row in await service.environment_breakdown()
        }

        assert providers == {"anthropic": 2, "openai": 1}
        assert environments == {"travel": 2, "banking": 1}

    async def test_evaluator_statistics_average_across_runs(self, db_session: AsyncSession) -> None:
        run_id = await _make_run(
            db_session, provider="anthropic", environment="travel", status="completed"
        )
        score_repo = EvaluationScoreRepository(db_session)
        await score_repo.create(
            run_id=run_id,
            evaluator_name="security",
            score=8.0,
            confidence=0.9,
            reasoning="r",
            evidence={},
            rubric_level="Strong",
            matched_criteria=[],
        )

        service = DashboardService(
            RunRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
        )
        stats = await service.evaluator_statistics()
        security_stats = next(s for s in stats if s["evaluator_name"] == "security")
        assert security_stats["average_score"] == pytest.approx(8.0)
        assert security_stats["count"] == 1
