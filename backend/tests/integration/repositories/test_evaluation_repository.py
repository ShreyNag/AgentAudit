"""Evaluation-side repositories, exercised independently of any Evaluation Engine logic.

Confirms the schema created in Phase 3 supports Phase 9's future writes without a migration
(docs/adr/0007-full-schema-upfront.md), while nothing here imports from app.evaluation.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.evaluation_repository import (
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.run_repository import RunRepository


async def _make_run(db_session: AsyncSession) -> int:
    task = await BenchmarkTaskRepository(db_session).create(
        task_id=f"banking-{uuid.uuid4().hex[:8]}",
        title="Transfer funds",
        description="Transfer $100 to savings.",
        environment="banking",
        difficulty="medium",
        instruction="Transfer $100 from checking to savings.",
        ground_truth={"expected_amount": 100},
        expected_tool_sequence=["bank_transfer"],
        task_metadata={},
    )
    run = await RunRepository(db_session).create(
        run_uuid=str(uuid.uuid4()),
        benchmark_task_id=task.id,
        provider="anthropic",
        model="claude-sonnet-5",
        environment="banking",
        status="completed",
    )
    return run.id


@pytest.mark.asyncio
class TestEvaluationRepositories:
    async def test_evaluation_report_round_trip(self, db_session: AsyncSession) -> None:
        run_id = await _make_run(db_session)
        repo = EvaluationReportRepository(db_session)
        await repo.create(
            run_id=run_id,
            overall_reasoning="All checks passed.",
            overall_summary="Safe and correct.",
            cts_raw=92.0,
            cts_reported=92.0,
            critical_failure=False,
            critical_failure_modules=[],
        )
        report = await repo.get_by_run(run_id)
        assert report is not None
        assert report.cts_raw == pytest.approx(92.0)
        assert report.cts_reported == pytest.approx(92.0)
        assert report.critical_failure is False
        assert report.critical_failure_modules == []

    async def test_evaluation_report_round_trips_a_critical_failure(
        self, db_session: AsyncSession
    ) -> None:
        run_id = await _make_run(db_session)
        repo = EvaluationReportRepository(db_session)
        await repo.create(
            run_id=run_id,
            overall_reasoning="Security critically failed.",
            overall_summary="Untrusted.",
            cts_raw=71.0,
            cts_reported=30.0,
            critical_failure=True,
            critical_failure_modules=["security"],
        )
        report = await repo.get_by_run(run_id)
        assert report is not None
        assert report.cts_raw == pytest.approx(71.0)
        assert report.cts_reported == pytest.approx(30.0)
        assert report.critical_failure is True
        assert report.critical_failure_modules == ["security"]

    async def test_average_cts_raw_means_the_uncapped_score_not_the_clamped_one(
        self, db_session: AsyncSession
    ) -> None:
        """Two runs, one a critical failure with cts_raw=71/cts_reported=30 and one a clean run
        at cts_raw=cts_reported=90, must average to (71+90)/2 -- never (30+90)/2. A mean over the
        clamped cts_reported column would be a mean over clamped numbers and not interpretable
        (docs/adr/0008-cts-cap-is-policy-not-metric.md)."""
        repo = EvaluationReportRepository(db_session)

        run_a = await _make_run(db_session)
        await repo.create(
            run_id=run_a,
            overall_reasoning="Security critically failed.",
            overall_summary="Untrusted.",
            cts_raw=71.0,
            cts_reported=30.0,
            critical_failure=True,
            critical_failure_modules=["security"],
        )
        run_b = await _make_run(db_session)
        await repo.create(
            run_id=run_b,
            overall_reasoning="All checks passed.",
            overall_summary="Safe and correct.",
            cts_raw=90.0,
            cts_reported=90.0,
            critical_failure=False,
            critical_failure_modules=[],
        )

        average = await repo.average_cts_raw()
        assert average == pytest.approx((71.0 + 90.0) / 2)

    async def test_evaluation_scores_are_unique_per_evaluator(
        self, db_session: AsyncSession
    ) -> None:
        run_id = await _make_run(db_session)
        repo = EvaluationScoreRepository(db_session)
        await repo.create(
            run_id=run_id,
            evaluator_name="security",
            score=0.95,
            confidence=0.9,
            reasoning="No unsafe tool calls detected.",
            evidence={},
            rubric_level="excellent",
            matched_criteria=["no_pii_leak"],
        )
        scores = await repo.list_by_run(run_id)
        assert len(scores) == 1
        fetched = await repo.get_by_run_and_evaluator(run_id, "security")
        assert fetched is not None
        assert fetched.score == pytest.approx(0.95)

    async def test_behaviour_and_failure_reports_round_trip(self, db_session: AsyncSession) -> None:
        run_id = await _make_run(db_session)
        behaviour_repo = BehaviourReportRepository(db_session)
        failure_repo = FailureReportRepository(db_session)

        await behaviour_repo.create(
            run_id=run_id,
            classification="SAFE_CORRECT",
            confidence=0.88,
            reasoning="Agent completed the task without unsafe actions.",
            evidence={},
        )
        await failure_repo.create(
            run_id=run_id,
            primary_failure="none",
            secondary_failures=[],
            affected_components=[],
            diagnostic_reasoning="No failure detected.",
            confidence=0.99,
        )

        behaviour = await behaviour_repo.get_by_run(run_id)
        failure = await failure_repo.get_by_run(run_id)
        assert behaviour is not None and behaviour.classification == "SAFE_CORRECT"
        assert failure is not None and failure.primary_failure == "none"
