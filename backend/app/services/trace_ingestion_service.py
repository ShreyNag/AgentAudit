"""``TraceIngestionService``: persist an externally-produced ``ExecutionTrace`` as a new run.

The counterpart to ``app.services.execution_service.ExecutionService`` for runs AgentAudit did
not execute itself: an agent traced in-process via ``app.trace.tracer.AgentAuditTracer``, or a
finished trace submitted to ``POST /api/v1/runs/external``. Reuses the exact persistence path
``ExecutionService`` uses (``app.services.trace_persistence.persist_trace_artifacts``), so a
persisted external trace is indistinguishable, from the Evaluation Engine's perspective, from
one AgentAudit executed itself -- nothing in ``app.evaluation`` changes to consume it.

Like ``ExecutionService``, this module never imports from ``app.evaluation``.
"""

from __future__ import annotations

import datetime as dt
import uuid

from app.core.exceptions import ValidationError
from app.models.benchmark_task import BenchmarkTaskModel
from app.models.run import RunModel
from app.repositories.benchmark_repository import BenchmarkTaskRepository
from app.repositories.run_repository import RunRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository
from app.services.base import BaseService
from app.services.trace_persistence import persist_trace_artifacts
from app.trace.models import ExecutionTrace


class TraceIngestionService(BaseService):
    """Persists a finished, externally-produced ``ExecutionTrace`` as a new run."""

    def __init__(
        self,
        run_repository: RunRepository,
        trace_repository: TraceRepository,
        trace_event_repository: TraceEventRepository,
        tool_call_repository: ToolCallRepository,
        tool_output_repository: ToolOutputRepository,
        benchmark_task_repository: BenchmarkTaskRepository,
    ) -> None:
        """Bind the service to every repository it persists ingested artifacts through."""
        self._run_repository = run_repository
        self._trace_repository = trace_repository
        self._trace_event_repository = trace_event_repository
        self._tool_call_repository = tool_call_repository
        self._tool_output_repository = tool_output_repository
        self._benchmark_task_repository = benchmark_task_repository

    async def ingest(
        self,
        *,
        trace: ExecutionTrace,
        environment: str,
        provider: str,
        model: str,
        task_id: str | None = None,
        status: str = "completed",
        task_instruction: str = "",
        ground_truth: dict[str, object] | None = None,
    ) -> RunModel:
        """Persist ``trace`` as a new run and return it.

        Args:
            trace: A finished ``ExecutionTrace``, typically from
                ``AgentAuditTracer.finish()``.
            environment: Free-form label for the kind of agent/system this run came from.
            provider: The agent's LLM provider, if known; otherwise a descriptive label.
            model: The agent's model, if known; otherwise a descriptive label.
            task_id: The benchmark task this run corresponds to, if any. When it matches an
                already-registered ``benchmark_tasks.task_id``, evaluation uses that task's real
                ground truth/expected tool sequence -- enabling direct comparison against an
                AgentAudit-executed run of the same task. Otherwise a placeholder task is
                created (or reused, if one was already created under this id).
            status: ``"completed"`` or ``"failed"``.
            task_instruction: Used only when creating a placeholder task (i.e. ``task_id`` is
                absent or unregistered), to give the Judge some task context; ignored when
                reusing an already-registered task, since tasks are immutable after publication.
            ground_truth: Same placeholder-only caveat as ``task_instruction``.

        Returns:
            The persisted run. Idempotent: re-submitting a trace with the same ``run_uuid``
            returns the already-persisted run rather than creating a duplicate.

        Raises:
            ValidationError: if ``trace.tool_calls`` and ``trace.tool_outputs`` are not
                pairwise matched (the same invariant ``ExecutionService`` relies on).
        """
        existing = await self._run_repository.get_by_uuid(trace.run_uuid)
        if existing is not None:
            return existing

        if len(trace.tool_calls) != len(trace.tool_outputs):
            raise ValidationError(
                "trace.tool_calls and trace.tool_outputs must be pairwise matched by index "
                f"(got {len(trace.tool_calls)} calls, {len(trace.tool_outputs)} outputs)."
            )

        task_row = await self._resolve_task(
            task_id=task_id,
            environment=environment,
            task_instruction=task_instruction,
            ground_truth=ground_truth or {},
        )

        now = dt.datetime.now(dt.UTC)
        run_row = await self._run_repository.create(
            run_uuid=trace.run_uuid,
            benchmark_task_id=task_row.id,
            provider=provider,
            model=model,
            environment=environment,
            status=status,
            execution_mode="external",
            start_time=now,
            end_time=now,
            execution_time=trace.statistics.get("execution_time_seconds"),
        )

        await persist_trace_artifacts(
            trace_repository=self._trace_repository,
            trace_event_repository=self._trace_event_repository,
            tool_call_repository=self._tool_call_repository,
            tool_output_repository=self._tool_output_repository,
            run_id=run_row.id,
            trace=trace,
        )
        return run_row

    async def _resolve_task(
        self,
        *,
        task_id: str | None,
        environment: str,
        task_instruction: str,
        ground_truth: dict[str, object],
    ) -> BenchmarkTaskModel:
        """Return the benchmark task ``task_id`` refers to, creating a placeholder if needed.

        ``runs.benchmark_task_id`` is a required foreign key (PROJECT_SPEC_1 SS80), so every
        ingested run needs a row here even when it wasn't run against a real benchmark task.
        """
        if task_id is not None:
            task_row = await self._benchmark_task_repository.get_by_task_id(task_id)
            if task_row is not None:
                return task_row

        placeholder_id = task_id or f"external-{uuid.uuid4()}"
        existing = await self._benchmark_task_repository.get_by_task_id(placeholder_id)
        if existing is not None:
            return existing
        return await self._benchmark_task_repository.create(
            task_id=placeholder_id,
            title=f"Externally traced run ({environment})",
            description=(
                "Auto-created placeholder for a run observed by AgentAuditTracer rather than "
                "executed by AgentAudit itself; there is no fixed ground truth unless supplied "
                "at ingestion time."
            ),
            environment=environment,
            difficulty="unknown",
            attack_type=None,
            instruction=task_instruction,
            ground_truth=ground_truth,
            expected_tool_sequence=[],
            task_metadata={"external": True},
        )
