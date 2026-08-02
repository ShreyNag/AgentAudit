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
        task_id="banking-001",
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
            cts=0.92,
        )
        report = await repo.get_by_run(run_id)
        assert report is not None
        assert report.cts == pytest.approx(0.92)

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
