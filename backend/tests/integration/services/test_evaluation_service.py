"""``EvaluationService`` end-to-end: load persisted trace -> evaluate -> persist full report.

Confirms Phase 9's decoupling acceptance criterion: evaluation runs entirely from a persisted
trace, using a separate DB write path from execution (PROJECT_SPEC_1 SS96/SS106).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import AgentAuditError
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.schemas import HealthCheckResult
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


class _UnhealthyFakeJudge(FakeJudgeProvider):
    """Reports itself unhealthy (e.g. the configured model isn't pulled) without ever being
    asked to actually judge anything -- proves evaluate_run() fails fast on this, rather than
    fanning out to all ten evaluators (each independently retrying) only to have every one of
    them fail the same way."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            provider=self.config.provider,
            healthy=False,
            message="Ollama is reachable, but model 'llama3.1:latest' is not pulled.",
        )


@pytest.fixture(autouse=True)
def _register_fake_judge() -> None:
    ProviderFactory.register("test-fake-judge", _StaticFakeJudge)
    ProviderFactory.register("test-unhealthy-judge", _UnhealthyFakeJudge)


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

    async def test_evaluate_run_records_the_judge_actually_used(
        self, db_session: AsyncSession
    ) -> None:
        """runs.judge_provider/judge_model must reflect the Judge genuinely used for this
        evaluation -- not whatever was set (or, for an externally-ingested run, never set) when
        the run was created. Covers both an unset run (TraceIngestionService never sets these)
        and a stale one (settings changed since the run was launched)."""
        run_id = await _seed_run_with_trace(db_session)
        run_repository = RunRepository(db_session)
        # Simulate an externally-ingested run, which never sets these at all.
        await run_repository.update(run_id, judge_provider=None, judge_model=None)

        service = EvaluationService(
            run_repository,
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

        await service.evaluate_run(run_id, settings)

        run_row = await run_repository.get(run_id)
        assert run_row is not None
        assert run_row.judge_provider == "test-fake-judge"
        assert run_row.judge_model == "fake-judge-model"

    async def test_evaluate_run_twice_replaces_the_prior_evaluation_instead_of_colliding(
        self, db_session: AsyncSession
    ) -> None:
        """POST /runs/{id}/evaluate is documented as re-runnable against a historical run
        (PROJECT_SPEC_1 SS98/SS106) -- evaluation_reports/evaluation_scores/behaviour_reports/
        failure_reports all have a unique constraint on run_id, so a second evaluation must
        replace the first's rows, not raise an IntegrityError on the duplicate key (reproduces
        the real failure: a client-perceived timeout whose evaluation had already actually
        persisted server-side, then retried)."""
        run_id = await _seed_run_with_trace(db_session)
        report_repository = EvaluationReportRepository(db_session)
        score_repository = EvaluationScoreRepository(db_session)
        behaviour_repository = BehaviourReportRepository(db_session)
        service = EvaluationService(
            RunRepository(db_session),
            TraceRepository(db_session),
            BenchmarkTaskRepository(db_session),
            report_repository,
            score_repository,
            behaviour_repository,
            FailureReportRepository(db_session),
        )
        settings = Settings(
            _env_file=None,
            judge_provider="test-fake-judge",
            judge_model="fake-judge-model",
            judge_api_key="x",
        )

        await service.evaluate_run(run_id, settings)
        await service.evaluate_run(run_id, settings)  # must not raise

        report = await report_repository.get_by_run(run_id)
        assert report is not None
        assert report.cts == pytest.approx(80.0)

        scores = await score_repository.list_by_run(run_id)
        assert len(scores) == 10  # not 20 -- the first evaluation's rows were replaced, not kept

        behaviour = await behaviour_repository.get_by_run(run_id)
        assert behaviour is not None

    async def test_evaluate_run_fails_fast_when_the_judge_is_unhealthy(
        self, db_session: AsyncSession
    ) -> None:
        """Reproduces the real 502 scenario: an Ollama judge whose model isn't pulled (or is
        otherwise unreachable) must fail immediately with one clear diagnostic, not after
        fanning out to all ten evaluators and burning through their retries first."""
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
            judge_provider="test-unhealthy-judge",
            judge_model="llama3.1:latest",
            judge_api_key="x",
        )

        with pytest.raises(AgentAuditError, match="not pulled"):
            await service.evaluate_run(run_id, settings)

        # No evaluation report should have been persisted for a run that never actually judged.
        report = await EvaluationReportRepository(db_session).get_by_run(run_id)
        assert report is None

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
