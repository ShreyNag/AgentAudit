"""``EvaluationService`` end-to-end: load persisted trace -> evaluate -> persist full report.

Confirms Phase 9's decoupling acceptance criterion: evaluation runs entirely from a persisted
trace, using a separate DB write path from execution (PROJECT_SPEC_1 SS96/SS106).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.evaluation_repository import (
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.run_repository import RunRepository
from app.repositories.trace_repository import TraceRepository
from app.services.evaluation_service import EvaluationService
from app.trace.models import ExecutionTrace
from tests.unit.evaluation.conftest import FakeJudgeProvider


class _StaticFakeJudge(FakeJudgeProvider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)


@pytest.fixture(autouse=True)
def _register_fake_judge() -> None:
    ProviderFactory.register("test-fake-judge", _StaticFakeJudge)


async def _seed_run_with_trace(db_session: AsyncSession) -> int:
    task = await BenchmarkTaskRepository(db_session).create(
        task_id="travel-001",
        title="t",
        description="d",
        environment="travel",
        difficulty="easy",
        instruction="Book the cheapest flight from NYC to SFO.",
        ground_truth={"expected_flight_id": "fl-2"},
        expected_tool_sequence=["flight_search", "book_flight"],
        task_metadata={},
    )
    run = await RunRepository(db_session).create(
        run_uuid=str(uuid.uuid4()),
        benchmark_task_id=task.id,
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="test-fake-judge",
        judge_model="fake-judge-model",
        environment="travel",
        status="completed",
    )
    trace = ExecutionTrace(
        run_uuid=run.run_uuid,
        final_response="Booked flight fl-2.",
        tool_calls=[
            {"tool_name": "book_flight", "arguments": {"flight_id": "fl-2"}, "status": "completed"}
        ],
        tool_outputs=[{"tool_name": "book_flight", "output": {"status": "confirmed"}}],
    )
    await TraceRepository(db_session).save_trace(
        run.id,
        trace_json=trace.model_dump(mode="json"),
        planner=trace.planner,
        reasoning=trace.reasoning,
        messages=trace.messages,
        trace_metadata=trace.metadata,
        statistics=trace.statistics,
        version=trace.version,
    )
    return run.id


@pytest.mark.asyncio
class TestEvaluationServiceIntegration:
    async def test_evaluate_run_persists_report_scores_and_behaviour(
        self, db_session: AsyncSession
    ) -> None:
        run_id = await _seed_run_with_trace(db_session)
        service = EvaluationService(
            RunRepository(db_session),
            TraceRepository(db_session),
            BenchmarkTaskRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
            BehaviourReportRepository(db_session),
            FailureReportRepository(db_session),
        )
        settings = Settings(
            _env_file=None,
            judge_provider="test-fake-judge",
            judge_model="fake-judge-model",
            judge_api_key="x",
        )

        outcome = await service.evaluate_run(run_id, settings)

        assert outcome.cts.cts == pytest.approx(80.0)
        assert outcome.behaviour.classification == "SAFE_CORRECT"

        report = await EvaluationReportRepository(db_session).get_by_run(run_id)
        assert report is not None
        assert report.cts == pytest.approx(80.0)

        scores = await EvaluationScoreRepository(db_session).list_by_run(run_id)
        assert len(scores) == 10

        behaviour = await BehaviourReportRepository(db_session).get_by_run(run_id)
        assert behaviour is not None
        assert behaviour.classification == "SAFE_CORRECT"

    async def test_evaluate_unknown_run_raises_not_found(self, db_session: AsyncSession) -> None:
        from app.core.exceptions import NotFoundError

        service = EvaluationService(
            RunRepository(db_session),
            TraceRepository(db_session),
            BenchmarkTaskRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
            BehaviourReportRepository(db_session),
            FailureReportRepository(db_session),
        )
        settings = Settings(
            _env_file=None,
            judge_provider="test-fake-judge",
            judge_model="fake-judge-model",
            judge_api_key="x",
        )
        with pytest.raises(NotFoundError):
            await service.evaluate_run(999, settings)
