"""``TraceIngestionService``: persist an externally-produced trace, then evaluate it unmodified.

Covers the core claim of external-agent tracing: a trace AgentAudit never executed is
indistinguishable, from the (entirely unmodified) Evaluation Engine's perspective, from one it
did.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import ValidationError
from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.engine import EvaluationEngine
from app.evaluation.evaluators.registry import build_default_registry
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.judge import JudgeService
from app.evaluation.rubric.loader import RubricLoader
from app.evaluation.scoring.cts import CTSCalculator
from app.providers.config import ProviderConfig
from app.repositories.benchmark_repository import (
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
)
from app.repositories.evaluation_repository import (
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.run_repository import RunRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.services.benchmark_service import BenchmarkService
from app.services.evaluation_service import EvaluationService
from app.services.trace_ingestion_service import TraceIngestionService
from app.trace.tracer import AgentAuditTracer
from tests.unit.evaluation.conftest import FakeJudgeProvider


def _make_ingestion_service(session: AsyncSession) -> TraceIngestionService:
    return TraceIngestionService(
        RunRepository(session),
        TraceRepository(session),
        TraceEventRepository(session),
        ToolCallRepository(session),
        ToolOutputRepository(session),
        BenchmarkTaskRepository(session),
    )


def _trace_an_independent_agent() -> object:
    tracer = AgentAuditTracer.start_run(task_id="trip_planner-001")
    tracer.record_llm_call(model="mock-llm", input="plan the trip", output="Searching flights.")
    tracer.record_tool_call(
        tool_name="flight_search",
        input={"destination": "Mumbai"},
        output={"flights": [{"id": "fl-2", "price": 480.0}]},
    )
    tracer.record_tool_call(
        tool_name="book_flight", input={"flight_id": "fl-2"},
        output={"booking_id": "booking-1", "status": "booked"},
    )
    return tracer.finish(final_output="Booked flight fl-2.", status="success")


@pytest.mark.asyncio
class TestTraceIngestionService:
    async def test_ingest_persists_run_trace_events_and_tool_calls(
        self, db_session: AsyncSession
    ) -> None:
        benchmark_service = BenchmarkService(
            BenchmarkTaskRepository(db_session), BenchmarkEnvironmentRepository(db_session)
        )
        await benchmark_service.ensure_seeded()

        trace = _trace_an_independent_agent()
        service = _make_ingestion_service(db_session)

        run_row = await service.ingest(
            trace=trace, environment="trip_planner", provider="external-mock-llm",
            model="mock-llm-1", task_id="trip_planner-001",
        )

        assert run_row.status == "completed"
        assert run_row.provider == "external-mock-llm"
        assert run_row.execution_mode == "external"
        # Before evaluation, no Judge has run yet -- the Run Details page must show "-- / --",
        # not fabricate a value. Only EvaluationService.evaluate_run() ever sets these, once a
        # Judge has actually been used (see test_evaluation_service.py).
        assert run_row.judge_provider is None
        assert run_row.judge_model is None

        trace_row = await TraceRepository(db_session).load_by_run(run_row.id)
        assert trace_row is not None
        assert trace_row.trace_json["final_response"] == "Booked flight fl-2."

        events = await TraceEventRepository(db_session).list_by_run(run_row.id)
        assert len(events) > 0

        tool_calls = await ToolCallRepository(db_session).list_by_run(run_row.id)
        assert [c.tool_name for c in tool_calls] == ["flight_search", "book_flight"]

    async def test_ingest_reuses_a_registered_task_for_ground_truth(
        self, db_session: AsyncSession
    ) -> None:
        benchmark_service = BenchmarkService(
            BenchmarkTaskRepository(db_session), BenchmarkEnvironmentRepository(db_session)
        )
        await benchmark_service.ensure_seeded()

        trace = _trace_an_independent_agent()
        service = _make_ingestion_service(db_session)
        run_row = await service.ingest(
            trace=trace, environment="trip_planner", provider="external", model="external",
            task_id="trip_planner-001",
        )

        task_row = await BenchmarkTaskRepository(db_session).get_by_task_id("trip_planner-001")
        assert task_row is not None
        assert run_row.benchmark_task_id == task_row.id

    async def test_ingest_creates_a_placeholder_task_for_an_unregistered_task_id(
        self, db_session: AsyncSession
    ) -> None:
        trace = _trace_an_independent_agent()
        service = _make_ingestion_service(db_session)

        run_row = await service.ingest(
            trace=trace, environment="ad_hoc_agent", provider="external", model="external",
            task_id=None, task_instruction="Book a trip to Mumbai.",
        )

        task_row = await BenchmarkTaskRepository(db_session).get(run_row.benchmark_task_id)
        assert task_row is not None
        assert task_row.instruction == "Book a trip to Mumbai."
        assert task_row.ground_truth == {}

    async def test_ingest_is_idempotent_for_the_same_run_uuid(
        self, db_session: AsyncSession
    ) -> None:
        trace = _trace_an_independent_agent()
        service = _make_ingestion_service(db_session)

        first = await service.ingest(
            trace=trace, environment="trip_planner", provider="external", model="external",
        )
        second = await service.ingest(
            trace=trace, environment="trip_planner", provider="external", model="external",
        )

        assert first.id == second.id

    async def test_ingest_rejects_mismatched_tool_calls_and_outputs(
        self, db_session: AsyncSession
    ) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer._recorder._tool_calls.append(  # noqa: SLF001 - deliberately corrupting the trace
            {"tool_name": "x", "arguments": {}, "status": "completed", "latency": None}
        )
        trace = tracer.finish()

        service = _make_ingestion_service(db_session)
        with pytest.raises(ValidationError):
            await service.ingest(
                trace=trace, environment="external", provider="external", model="external",
            )

    async def test_ingested_external_trace_is_evaluable_by_the_unmodified_evaluation_engine(
        self, db_session: AsyncSession
    ) -> None:
        """The end-to-end claim: an externally traced run reaches the same, unmodified
        Evaluation Engine and produces real evaluator scores + a Composite Trust Score."""
        benchmark_service = BenchmarkService(
            BenchmarkTaskRepository(db_session), BenchmarkEnvironmentRepository(db_session)
        )
        await benchmark_service.ensure_seeded()

        trace = _trace_an_independent_agent()
        ingestion_service = _make_ingestion_service(db_session)
        run_row = await ingestion_service.ingest(
            trace=trace, environment="trip_planner", provider="external-mock-llm",
            model="mock-llm-1", task_id="trip_planner-001",
        )

        engine = EvaluationEngine(
            build_default_registry(),
            BehaviourClassifier(),
            FailureAttributionEngine(),
            CTSCalculator(),
            EvidenceExtractor(),
            RubricLoader(),
        )
        judge = JudgeService(
            FakeJudgeProvider(ProviderConfig(provider="openai", model="gpt-5", api_key="x"))
        )
        from app.evaluation.context import EvaluationContext
        from app.trace.models import ExecutionTrace

        trace_row = await TraceRepository(db_session).load_by_run(run_row.id)
        assert trace_row is not None
        task_row = await BenchmarkTaskRepository(db_session).get(run_row.benchmark_task_id)
        assert task_row is not None
        context = EvaluationContext(
            run_id=run_row.id,
            execution_trace=ExecutionTrace.model_validate(trace_row.trace_json),
            task_instruction=task_row.instruction,
            ground_truth=task_row.ground_truth,
            environment=run_row.environment,
            provider=run_row.provider,
            model=run_row.model,
            judge_provider="openai",
            judge_model="gpt-5",
            statistics=dict(trace_row.statistics),
            expected_tool_sequence=list(task_row.expected_tool_sequence),
        )

        outcome = await engine.run(context, judge)

        assert len(outcome.evaluator_results) == 10
        assert outcome.cts.cts is not None
        assert outcome.behaviour.classification

    async def test_evaluation_service_evaluate_run_works_unmodified_on_an_ingested_run(
        self, db_session: AsyncSession
    ) -> None:
        """Same claim as above, but through the actual public ``EvaluationService`` -- no code
        under test here has been touched to support external traces."""
        benchmark_service = BenchmarkService(
            BenchmarkTaskRepository(db_session), BenchmarkEnvironmentRepository(db_session)
        )
        await benchmark_service.ensure_seeded()

        trace = _trace_an_independent_agent()
        ingestion_service = _make_ingestion_service(db_session)
        run_row = await ingestion_service.ingest(
            trace=trace, environment="trip_planner", provider="external-mock-llm",
            model="mock-llm-1", task_id="trip_planner-001",
        )

        from app.providers.factory import ProviderFactory

        ProviderFactory.register("ingestion-test-fake-judge", FakeJudgeProvider)
        settings = Settings(
            _env_file=None, judge_provider="ingestion-test-fake-judge",
            judge_model="fake-judge-model", judge_api_key="x",
        )

        evaluation_service = EvaluationService(
            RunRepository(db_session),
            TraceRepository(db_session),
            BenchmarkTaskRepository(db_session),
            EvaluationReportRepository(db_session),
            EvaluationScoreRepository(db_session),
            BehaviourReportRepository(db_session),
            FailureReportRepository(db_session),
        )

        outcome = await evaluation_service.evaluate_run(run_row.id, settings)

        assert outcome.cts.cts is not None
        report = await evaluation_service.get_report(run_row.id)
        assert report.cts == outcome.cts.cts
