"""``ExecutionRunner`` (PROJECT_SPEC_1 SS32/SS48, PROJECT_SPEC_2 SS69-72;

see ``docs/adr/0001-*.md``).

The top-level entry point the service layer calls: resolves the task's environment, provider,
and available tools, builds the :class:`~app.execution.context.ExecutionContext`, and hands off
to :class:`~app.execution.common_agent_executor.CommonAgentExecutor`. Performs no evaluation.
"""

from __future__ import annotations

from app.benchmark.models import Task
from app.benchmark.registry import BenchmarkRegistry
from app.environments.registry import EnvironmentRegistry
from app.execution.common_agent_executor import CommonAgentExecutor
from app.execution.config import ExecutionConfig
from app.execution.context import ExecutionContext
from app.execution.planner import ExecutionPlanner
from app.execution.result import ExecutionResult
from app.providers.base import BaseProvider
from app.tools.registry import ToolRegistry
from app.trace.recorder import TraceRecorder


class ExecutionRunner:
    """Orchestrates one full benchmark execution, end to end, with zero evaluation logic."""

    def __init__(
        self,
        environment_registry: EnvironmentRegistry,
        tool_registry: ToolRegistry,
        benchmark_registry: BenchmarkRegistry,
    ) -> None:
        """Bind the runner to the registries it resolves tasks' dependencies through."""
        self._environment_registry = environment_registry
        self._tool_registry = tool_registry
        self._benchmark_registry = benchmark_registry

    async def run(
        self,
        *,
        run_uuid: str,
        task: Task,
        provider: BaseProvider,
        config: ExecutionConfig | None = None,
    ) -> tuple[ExecutionResult, TraceRecorder]:
        """Execute ``task`` against ``provider`` and return its result and full trace recorder.

        Args:
            run_uuid: The externally-facing identifier for this run (matches ``runs.run_uuid``).
            task: The validated benchmark task to execute.
            provider: An already-initialized provider adapter for the Agent Under Test.
            config: Execution-loop configuration; defaults applied when omitted.

        Returns:
            A tuple of the execution result and the trace recorder holding every recorded event,
            ready for :mod:`app.trace` to persist.
        """
        config = config or ExecutionConfig()
        environment = await self._environment_registry.create(task.environment)
        environment_meta = self._benchmark_registry.get(task.environment)
        trace_recorder = TraceRecorder(run_uuid=run_uuid)

        context = ExecutionContext(
            run_uuid=run_uuid,
            task=task,
            environment=environment,
            provider=provider,
            tool_registry=self._tool_registry,
            trace_recorder=trace_recorder,
            available_tools=environment_meta.toolset,
            config=config,
        )
        planner = ExecutionPlanner(config)
        executor = CommonAgentExecutor(context, planner)

        try:
            result = await executor.run()
        finally:
            await environment.cleanup()

        return result, trace_recorder
