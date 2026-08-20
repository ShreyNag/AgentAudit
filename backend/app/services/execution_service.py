"""``ExecutionService`` (PROJECT_SPEC_2 SS86): launch, run, and persist one benchmark execution.

The primary orchestration service. Persists the run, trace, tool calls, and tool outputs
immediately after execution completes (PROJECT_SPEC_1 SS97) and returns before any evaluation
occurs -- this module never imports from :mod:`app.evaluation` (PROJECT_SPEC_1 SS106).
"""

from __future__ import annotations

import datetime as dt
import uuid

# Importing these packages triggers environment and tool registration as a side effect.
import app.environments  # noqa: F401
import app.tools.implementations  # noqa: F401
from app.benchmark.models import Task
from app.benchmark.registry import benchmark_registry
from app.benchmark.validator import BenchmarkValidator
from app.config import Settings
from app.core.exceptions import NotFoundError
from app.environments.registry import environment_registry
from app.execution.config import ExecutionConfig
from app.execution.result import ExecutionResult
from app.execution.runner import ExecutionRunner
from app.models.run import RunModel
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.run_repository import RunRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.services.base import BaseService
from app.services.trace_persistence import persist_trace_artifacts
from app.tools.registry import tool_registry


class ExecutionService(BaseService):
    """Launches a benchmark task against a provider and persists the complete result."""

    def __init__(
        self,
        run_repository: RunRepository,
        trace_repository: TraceRepository,
        trace_event_repository: TraceEventRepository,
        tool_call_repository: ToolCallRepository,
        tool_output_repository: ToolOutputRepository,
        benchmark_task_repository: BenchmarkTaskRepository,
    ) -> None:
        """Bind the service to every repository it persists execution artifacts through."""
        self._run_repository = run_repository
        self._trace_repository = trace_repository
        self._trace_event_repository = trace_event_repository
        self._tool_call_repository = tool_call_repository
        self._tool_output_repository = tool_output_repository
        self._benchmark_task_repository = benchmark_task_repository
        self._validator = BenchmarkValidator(benchmark_registry, tool_registry)

    async def launch(
        self,
        *,
        task_id: str,
        settings: Settings,
        provider_name: str | None = None,
        model: str | None = None,
        execution_config: ExecutionConfig | None = None,
    ) -> tuple[RunModel, ExecutionResult]:
        """Execute the benchmark task ``task_id`` and persist the full result.

        Args:
            task_id: External identifier of a persisted ``benchmark_tasks`` row.
            settings: Application settings, supplying default AUT provider/model/credentials.
            provider_name: Overrides ``settings.aut_provider`` for this run, if given.
            model: Overrides ``settings.aut_model`` for this run, if given.
            execution_config: Overrides default execution-loop limits, if given.

        Returns:
            The persisted :class:`~app.models.run.RunModel` and the in-memory
            :class:`~app.execution.result.ExecutionResult`.

        Raises:
            NotFoundError: if ``task_id`` does not exist.
            ValidationError: if the task fails pre-execution validation (PROJECT_SPEC_2 SS113).
        """
        task_row = await self._benchmark_task_repository.get_by_task_id(task_id)
        if task_row is None:
            raise NotFoundError(f"No benchmark task registered under '{task_id}'.")

        task = Task(
            task_id=task_row.task_id,
            title=task_row.title,
            description=task_row.description,
            environment=task_row.environment,
            difficulty=task_row.difficulty,
            instruction=task_row.instruction,
            ground_truth=task_row.ground_truth,
            expected_tool_sequence=list(task_row.expected_tool_sequence),
            attack_type=task_row.attack_type,
            metadata=task_row.task_metadata,
        )
        self._validator.validate(task)

        provider_config = ProviderConfig(
            provider=provider_name or settings.aut_provider,
            model=model or settings.aut_model,
            api_key=settings.aut_api_key,
            base_url=settings.aut_base_url,
        )
        provider = await ProviderFactory.create(provider_config)

        run_uuid = str(uuid.uuid4())
        run_row = await self._run_repository.create(
            run_uuid=run_uuid,
            benchmark_task_id=task_row.id,
            provider=provider_config.provider,
            model=provider_config.model,
            judge_provider=settings.judge_provider,
            judge_model=settings.judge_model,
            environment=task.environment,
            status="running",
            start_time=dt.datetime.now(dt.UTC),
        )

        runner = ExecutionRunner(environment_registry, tool_registry, benchmark_registry)
        try:
            result, recorder = await runner.run(
                run_uuid=run_uuid, task=task, provider=provider, config=execution_config
            )
        finally:
            await provider.shutdown()

        trace = recorder.finalize(
            task=task,
            environment_name=task.environment,
            provider_name=provider_config.provider,
            model_name=provider_config.model,
            final_response=result.final_response,
            statistics=result.statistics,
        )

        run_row = await self._run_repository.update(
            run_row.id,
            status=result.status,
            execution_time=result.statistics.execution_time_seconds,
            end_time=dt.datetime.now(dt.UTC),
        )
        assert run_row is not None  # the row we just created cannot vanish mid-request

        await persist_trace_artifacts(
            trace_repository=self._trace_repository,
            trace_event_repository=self._trace_event_repository,
            tool_call_repository=self._tool_call_repository,
            tool_output_repository=self._tool_output_repository,
            run_id=run_row.id,
            trace=trace,
        )

        return run_row, result
