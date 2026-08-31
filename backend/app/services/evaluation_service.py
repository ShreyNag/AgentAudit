"""``EvaluationService`` (PROJECT_SPEC_2 SS88): load trace -> evaluate -> persist scores/CTS.

Never executes a benchmark (PROJECT_SPEC_2 SS88) and never imports from :mod:`app.execution`,
:mod:`app.environments`, or :mod:`app.tools` -- it only ever reads a persisted trace and the
Judge provider. Uses its own repositories/session, never sharing a transaction with
:class:`~app.services.execution_service.ExecutionService` (PROJECT_SPEC_1 SS96).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.config import Settings
from app.core.exceptions import NotFoundError, TraceError
from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.context import EvaluationContext
from app.evaluation.engine import EvaluationEngine
from app.evaluation.evaluators.registry import build_default_registry
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.judge import JudgeService
from app.evaluation.models import EvaluationOutcome
from app.evaluation.rubric.loader import RubricLoader
from app.evaluation.scoring.cts import CTSCalculator
from app.models.behaviour_report import BehaviourReportModel
from app.models.evaluation_report import EvaluationReportModel
from app.models.evaluation_score import EvaluationScoreModel
from app.models.failure_report import FailureReportModel
from app.models.run import RunModel
from app.providers.exceptions import ProviderUnavailableError
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
from app.services.base import BaseService
from app.trace.models import ExecutionTrace


class EvaluationService(BaseService):
    """Evaluates a persisted run's execution trace and persists the full evaluation report."""

    def __init__(
        self,
        run_repository: RunRepository,
        trace_repository: TraceRepository,
        benchmark_task_repository: BenchmarkTaskRepository,
        evaluation_report_repository: EvaluationReportRepository,
        evaluation_score_repository: EvaluationScoreRepository,
        behaviour_report_repository: BehaviourReportRepository,
        failure_report_repository: FailureReportRepository,
    ) -> None:
        """Bind the service to every repository it reads from or persists evaluation data to."""
        self._run_repository = run_repository
        self._trace_repository = trace_repository
        self._benchmark_task_repository = benchmark_task_repository
        self._evaluation_report_repository = evaluation_report_repository
        self._evaluation_score_repository = evaluation_score_repository
        self._behaviour_report_repository = behaviour_report_repository
        self._failure_report_repository = failure_report_repository
        self._engine = EvaluationEngine(
            build_default_registry(),
            BehaviourClassifier(),
            FailureAttributionEngine(),
            CTSCalculator(),
            EvidenceExtractor(),
            RubricLoader(),
        )

    async def _build_context(self, run_row: RunModel) -> EvaluationContext:
        trace_row = await self._trace_repository.load_by_run(run_row.id)
        if trace_row is None:
            raise TraceError(f"No execution trace persisted for run_id {run_row.id}.")
        task_row = await self._benchmark_task_repository.get(run_row.benchmark_task_id)
        if task_row is None:
            raise NotFoundError(f"No benchmark task with id {run_row.benchmark_task_id}.")

        # trace_json is the full serialized ExecutionTrace (PROJECT_SPEC_2 SS81), so it can be
        # reconstructed in one step rather than reassembled field-by-field from the other columns.
        trace = ExecutionTrace.model_validate(trace_row.trace_json)

        return EvaluationContext(
            run_id=run_row.id,
            execution_trace=trace,
            task_instruction=task_row.instruction,
            ground_truth=task_row.ground_truth,
            environment=run_row.environment,
            provider=run_row.provider,
            model=run_row.model,
            judge_provider=run_row.judge_provider or "",
            judge_model=run_row.judge_model or "",
            statistics=dict(trace_row.statistics),
            expected_tool_sequence=list(task_row.expected_tool_sequence),
            attack_type=task_row.attack_type,
        )

    async def evaluate_run(self, run_id: int, settings: Settings) -> EvaluationOutcome:
        """Evaluate the persisted trace for ``run_id`` and persist the full evaluation report.

        Raises:
            NotFoundError: if no run exists with the given ``run_id``.
            TraceError: if no execution trace has been persisted for the run.
        """
        run_row = await self._run_repository.get(run_id)
        if run_row is None:
            raise NotFoundError(f"No run with id {run_id}.")

        context = await self._build_context(run_row)

        judge_provider = await ProviderFactory.create_judge(settings)
        judge = JudgeService(judge_provider)
        try:
            # Fail fast with one clear diagnostic instead of fanning out to all ten evaluators
            # (each independently retrying up to max_retries times) only to have every one of
            # them fail the same way -- the exact multi-minute hang-then-500 this was added to
            # prevent. For OllamaProvider this also confirms the configured model is actually
            # pulled, not just that the server is reachable (app/providers/ollama_provider.py).
            health = await judge_provider.health_check()
            if not health.healthy:
                raise ProviderUnavailableError(
                    f"Judge provider '{settings.judge_provider}' ({settings.judge_model}) is "
                    f"not available: {health.message or 'health check failed.'}"
                )
            outcome = await self._engine.run(context, judge)
        finally:
            await judge_provider.shutdown()

        await self._persist(run_id, outcome)
        # Record which Judge actually evaluated this run. runs.judge_provider/judge_model are
        # otherwise only ever set once, at run-creation time (ExecutionService.launch()) --
        # never for an externally-ingested run (TraceIngestionService.ingest() sets neither),
        # and never refreshed if .env's JUDGE_* settings changed between launch and evaluation.
        # This is the one place that reflects the Judge genuinely used, for every execution mode.
        await self._run_repository.update(
            run_id, judge_provider=settings.judge_provider, judge_model=settings.judge_model
        )
        return outcome

    async def get_report(self, run_id: int) -> EvaluationReportModel:
        """Return the persisted evaluation report for ``run_id``.

        Raises:
            NotFoundError: if the run has not yet been evaluated.
        """
        report = await self._evaluation_report_repository.get_by_run(run_id)
        if report is None:
            raise NotFoundError(f"No evaluation report persisted for run_id {run_id}.")
        return report

    async def get_scores(self, run_id: int) -> Sequence[EvaluationScoreModel]:
        """Return every evaluator's persisted score for ``run_id``."""
        return await self._evaluation_score_repository.list_by_run(run_id)

    async def get_behaviour(self, run_id: int) -> BehaviourReportModel:
        """Return the persisted behavioural classification for ``run_id``.

        Raises:
            NotFoundError: if the run has not yet been evaluated.
        """
        behaviour = await self._behaviour_report_repository.get_by_run(run_id)
        if behaviour is None:
            raise NotFoundError(f"No behaviour classification persisted for run_id {run_id}.")
        return behaviour

    async def get_failure(self, run_id: int) -> FailureReportModel:
        """Return the persisted failure attribution for ``run_id``.

        Raises:
            NotFoundError: if the run was not evaluated, or had no attributable failure.
        """
        failure = await self._failure_report_repository.get_by_run(run_id)
        if failure is None:
            raise NotFoundError(f"No failure attribution persisted for run_id {run_id}.")
        return failure

    async def _persist(self, run_id: int, outcome: EvaluationOutcome) -> None:
        # POST /runs/{id}/evaluate is explicitly documented as re-runnable against a historical
        # run (PROJECT_SPEC_1 SS98/SS106) -- every one of these four tables has a unique
        # constraint on run_id, so a second evaluation must replace the first, not collide with
        # it (previously an unhandled IntegrityError on retry after any earlier successful
        # evaluation, e.g. a client-perceived timeout that had actually already persisted one).
        await self._evaluation_report_repository.delete_by_run(run_id)
        await self._evaluation_score_repository.delete_by_run(run_id)
        await self._behaviour_report_repository.delete_by_run(run_id)
        await self._failure_report_repository.delete_by_run(run_id)

        overall_reasoning = "\n\n".join(
            f"{result.evaluator_name}: {result.reasoning}" for result in outcome.evaluator_results
        )
        summaries = {
            result.evaluator_name: result.reasoning for result in outcome.evaluator_results
        }

        await self._evaluation_report_repository.create(
            run_id=run_id,
            overall_reasoning=overall_reasoning,
            overall_summary=outcome.cts.summary,
            cts=outcome.cts.cts,
            planner_summary=summaries.get("planner"),
            security_summary=summaries.get("security"),
            integrity_summary=summaries.get("integrity"),
        )

        for result in outcome.evaluator_results:
            await self._evaluation_score_repository.create(
                run_id=run_id,
                evaluator_name=result.evaluator_name,
                score=result.score,
                confidence=result.confidence,
                reasoning=result.reasoning,
                expected_outcome=result.expected_outcome,
                actual_outcome=result.actual_outcome,
                evidence=[item.model_dump(mode="json") for item in result.evidence],
                rubric_level=result.matched_rubric,
                # "matched_criteria" (PROJECT_SPEC_1 SS86) is populated from the evaluator's
                # observed strengths -- the rubric criteria the run was judged to have satisfied.
                matched_criteria=result.strengths,
                criteria_assessment=[
                    item.model_dump(mode="json") for item in result.criteria_assessment
                ],
            )

        await self._behaviour_report_repository.create(
            run_id=run_id,
            classification=outcome.behaviour.classification,
            confidence=outcome.behaviour.confidence,
            reasoning=outcome.behaviour.reasoning,
            evidence=outcome.behaviour.supporting_evidence,
        )

        if outcome.failure is not None:
            await self._failure_report_repository.create(
                run_id=run_id,
                primary_failure=outcome.failure.primary_failure,
                secondary_failures=outcome.failure.secondary_failures,
                affected_components=outcome.failure.affected_components,
                diagnostic_reasoning=outcome.failure.reasoning,
                confidence=outcome.failure.confidence,
            )
