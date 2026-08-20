"""``AgentAuditTracer``: observes an independently running LLM-based agent.

Distinct from ``app.execution.common_agent_executor.CommonAgentExecutor``, which *drives* a
benchmark execution AgentAudit itself controls: this module never calls an LLM, never invokes a
tool, and never decides what the agent should do next. It only records events the host
application chooses to report -- an LLM call it already made, a tool call it already ran -- and
assembles them into the exact same ``app.trace.models.ExecutionTrace`` the internal execution
engine produces (via the shared ``app.trace.recorder.TraceRecorder``), so the Evaluation Engine
requires no changes to consume either one (PROJECT_SPEC_1 SS106).

Framework/provider-agnostic by construction: every method accepts plain Python objects (strings,
dicts), not any AgentAudit- or vendor-specific type, so it integrates with any agent -- a
chatbot, a RAG pipeline, a coding agent, a LangGraph/CrewAI/AutoGen/OpenAI-Agents-SDK graph, or a
fully custom loop -- without requiring that agent to adopt AgentAudit's internal types.
"""

from __future__ import annotations

import datetime as dt
import functools
import inspect
import time
import uuid
from collections.abc import Callable
from typing import Any, Literal, ParamSpec, TypeVar

from app.core.logging import get_logger
from app.trace.models import ExecutionTrace
from app.trace.recorder import TraceRecorder

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

#: ``"strict"`` re-raises any error encountered while recording (useful in tests/CI, where a
#: broken tracer call should fail loudly). ``"best_effort"`` (the default) logs and swallows it
#: instead, since a tracing bug must never take down the agent being observed.
TracerMode = Literal["strict", "best_effort"]


class AgentAuditTracer:
    """Records one independently running agent's execution as an ``ExecutionTrace``.

    Usage::

        tracer = AgentAuditTracer.start_run(task_id="trip_planner-001")
        tracer.record_llm_call(model="gpt-5", input=prompt, output=response_text)
        tracer.record_tool_call(tool_name="flight_search", input={"destination": "Mumbai"},
                                 output={"flights": [...]})
        trace = tracer.finish(final_output="Booked flight fl-2.", status="success")

    ``trace`` is then handed to ``app.services.trace_ingestion_service.TraceIngestionService``
    (in-process) or POSTed to ``POST /api/v1/runs/external`` (out-of-process), either of which
    persists it through the same path a normal benchmark run uses, making it immediately
    evaluable via the existing ``POST /api/v1/runs/{run_id}/evaluate``.
    """

    def __init__(
        self,
        run_id: str | None = None,
        *,
        task_id: str | None = None,
        parent_run_id: str | None = None,
        agent_name: str | None = None,
        agent_id: str | None = None,
        environment: str = "external",
        mode: TracerMode = "best_effort",
    ) -> None:
        """Start observing a new run.

        Args:
            run_id: Externally-facing run identifier; a UUID4 is generated if omitted.
            task_id: The benchmark/task this run corresponds to, if any -- when it matches an
                already-registered ``benchmark_tasks.task_id``, ingestion evaluates this run
                against that task's real ground truth, enabling direct comparison against an
                AgentAudit-executed run of the same task.
            parent_run_id: The parent run's id, for a sub-agent/nested-agent invocation.
            agent_name: A human-readable name for the independently running agent itself (e.g.
                ``"support-chatbot-v3"``), distinct from ``environment``'s category label.
            agent_id: A stable identifier for the agent/deployment, if the host application has
                one (e.g. a service name or version tag), distinct from this run's ``run_id``.
            environment: A free-form label for what kind of agent/system this is (e.g.
                ``"trip_planner"``, ``"support_chatbot"``, ``"coding_agent"``); unlike the
                internal execution engine's ``environment``, this is never validated against a
                registered ``BenchmarkEnvironment`` since the agent doesn't run inside one.
            mode: ``"strict"`` or ``"best_effort"`` (default) -- see ``TracerMode``.
        """
        self.run_id = run_id or str(uuid.uuid4())
        self.task_id = task_id
        self.parent_run_id = parent_run_id
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.environment = environment
        self.mode: TracerMode = mode
        self._recorder = TraceRecorder(run_uuid=self.run_id)
        self._finished = False
        self._recorder.record_run_started()
        self._start_time = dt.datetime.now(dt.UTC)

    @classmethod
    def start_run(
        cls,
        run_id: str | None = None,
        *,
        task_id: str | None = None,
        parent_run_id: str | None = None,
        agent_name: str | None = None,
        agent_id: str | None = None,
        environment: str = "external",
        mode: TracerMode = "best_effort",
    ) -> AgentAuditTracer:
        """Start observing a new run. Equivalent to the constructor."""
        return cls(
            run_id,
            task_id=task_id,
            parent_run_id=parent_run_id,
            agent_name=agent_name,
            agent_id=agent_id,
            environment=environment,
            mode=mode,
        )

    def _guard(self, operation: str, fn: Callable[[], object]) -> None:
        """Run a recording call according to ``self.mode``.

        A tracing failure must never break the agent it observes in production use -- but must
        never be silently invisible either, so it is always logged even when swallowed.
        """
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring above
            if self.mode == "strict":
                raise
            logger.warning(
                "agentaudit_tracer_recording_failed",
                operation=operation,
                run_id=self.run_id,
                error=str(exc),
            )

    def record_llm_call(
        self,
        *,
        model: str,
        input: Any,  # noqa: A002 - matches PROJECT_SPEC_1 SS59 field name
        output: Any,
        provider: str = "external",
        latency: float | None = None,
        usage: dict[str, Any] | None = None,
        reasoning: str | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Record one LLM call the observed agent made with its own provider/SDK.

        Args:
            model: The model name/identifier the agent used.
            input: The prompt/messages sent to the model, in whatever shape the agent has them.
            output: The model's response (text, or a structured dict for tool-call-shaped
                responses); pass whatever the agent's own SDK returned.
            provider: The LLM vendor, if known (``"openai"``, ``"anthropic"``, ...); defaults to
                ``"external"`` when the observed agent's provider isn't AgentAudit's concern.
            latency: Call duration in seconds, if measured.
            usage: Token usage/cost info in whatever shape the agent's SDK reports it, if any.
            reasoning: The model's stated reasoning for this turn, only if the agent actually
                captured one distinct from ``output`` -- never inferred or fabricated.
            metadata: Any additional context worth keeping on the trace event.
            error: Set when the call itself failed (the request errored, not just a bad answer).
        """
        self._guard(
            "record_llm_call",
            lambda: self._recorder.record_llm_call(
                provider=provider,
                model=model,
                input=input,
                output=output,
                latency=latency,
                usage=usage,
                reasoning=reasoning,
                metadata=metadata,
                status="failed" if error else "ok",
                error=error,
            ),
        )

    def record_tool_call(
        self,
        *,
        tool_name: str,
        input: dict[str, Any],  # noqa: A002
        output: Any = None,
        error: str | None = None,
        latency: float | None = None,
        metadata: dict[str, Any] | None = None,
        call_id: str | None = None,
    ) -> None:
        """Record one tool invocation the observed agent performed, proposal and result together.

        Use ``record_tool_proposed``/``record_tool_result`` instead when the agent's proposal
        (what the LLM asked for) and its execution (what actually ran) happen at different
        points in your code -- e.g. inside ``trace_tool``.
        """
        self._guard(
            "record_tool_call",
            lambda: self._recorder.record_tool_call(
                tool_name=tool_name,
                input=input,
                output=output,
                error=error,
                latency=latency,
                metadata=metadata,
                call_id=call_id,
            ),
        )

    def record_tool_proposed(
        self,
        *,
        tool_name: str,
        input: dict[str, Any],  # noqa: A002
        call_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record that a tool call was proposed (e.g. by the LLM), before it executes.

        Returns the call id to pass back into ``record_tool_result`` so the two are linked.
        """
        call_id = call_id or str(uuid.uuid4())
        self._guard(
            "record_tool_proposed",
            lambda: self._recorder.record_tool_proposed(
                tool_name=tool_name, input=input, call_id=call_id, metadata=metadata
            ),
        )
        return call_id

    def record_tool_result(
        self,
        *,
        tool_name: str,
        input: dict[str, Any],  # noqa: A002
        output: Any = None,
        error: str | None = None,
        latency: float | None = None,
        call_id: str | None = None,
    ) -> None:
        """Record the outcome of a previously proposed tool call, successful or not."""
        self._guard(
            "record_tool_result",
            lambda: self._recorder.record_tool_result(
                tool_name=tool_name,
                input=input,
                output=output,
                error=error,
                latency=latency,
                call_id=call_id,
            ),
        )

    def record_event(
        self,
        *,
        step_type: str,
        name: str | None = None,
        input: Any = None,  # noqa: A002
        output: Any = None,
        metadata: dict[str, Any] | None = None,
        status: str = "ok",
        error: str | None = None,
    ) -> None:
        """Record any agent/step event with no dedicated event type: a planning step, a memory
        read, a retrieval call, a sub-agent handoff, etc.
        """
        self._guard(
            "record_event",
            lambda: self._recorder.record_agent_step(
                step_type=step_type,
                name=name,
                input=input,
                output=output,
                metadata=metadata,
                status=status,
                error=error,
            ),
        )

    def record_error(self, error: str | Exception) -> None:
        """Record a run-level error that isn't tied to one specific LLM or tool call."""
        exc = error if isinstance(error, Exception) else RuntimeError(str(error))
        self._guard("record_error", lambda: self._recorder.record_error(exc))

    def trace_tool(
        self, name: str | None = None
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator that traces a tool function's proposal, execution, and result/error.

        Works for both sync and async callables::

            @tracer.trace_tool()
            def search_database(query: str) -> list[dict]:
                ...

        The tool name defaults to the wrapped function's ``__name__``. Arguments are bound via
        ``inspect.signature`` so both positional and keyword calls produce a named-arguments
        dict in the trace. The wrapped function's own exceptions always propagate -- tracing an
        error never suppresses it, only records it (per ``mode``, recording itself never breaks
        the call).
        """

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            tool_name = name or fn.__name__
            signature = inspect.signature(fn)

            if inspect.iscoroutinefunction(fn):

                @functools.wraps(fn)
                async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    arguments = _bind_arguments(signature, args, kwargs)
                    call_id = self.record_tool_proposed(tool_name=tool_name, input=arguments)
                    start = time.perf_counter()
                    try:
                        result = await fn(*args, **kwargs)
                    except Exception as exc:
                        self.record_tool_result(
                            tool_name=tool_name, input=arguments, error=str(exc),
                            latency=time.perf_counter() - start, call_id=call_id,
                        )
                        raise
                    self.record_tool_result(
                        tool_name=tool_name, input=arguments, output=result,
                        latency=time.perf_counter() - start, call_id=call_id,
                    )
                    return result  # type: ignore[no-any-return]

                return async_wrapper  # type: ignore[return-value]

            @functools.wraps(fn)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                arguments = _bind_arguments(signature, args, kwargs)
                call_id = self.record_tool_proposed(tool_name=tool_name, input=arguments)
                start = time.perf_counter()
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:
                    self.record_tool_result(
                        tool_name=tool_name, input=arguments, error=str(exc),
                        latency=time.perf_counter() - start, call_id=call_id,
                    )
                    raise
                self.record_tool_result(
                    tool_name=tool_name, input=arguments, output=result,
                    latency=time.perf_counter() - start, call_id=call_id,
                )
                return result

            return sync_wrapper

        return decorator

    def finish(self, *, final_output: str | None = None, status: str = "success") -> ExecutionTrace:
        """Mark the run complete and assemble the full ``ExecutionTrace``.

        Args:
            final_output: The agent's final answer/result, if any.
            status: ``"success"`` or ``"error"`` (this tracer's own vocabulary); mapped onto the
                trace's internal ``"completed"``/``"failed"`` status so downstream
                persistence/evaluation see the same values a normal benchmark run would.

        Raises:
            RuntimeError: if called more than once for the same tracer.
        """
        if self._finished:
            raise RuntimeError(f"AgentAuditTracer for run '{self.run_id}' has already finished.")
        self._finished = True
        internal_status = "completed" if status == "success" else "failed"
        self._recorder.record_run_completed(internal_status)
        statistics = {
            "execution_time_seconds": (
                dt.datetime.now(dt.UTC) - self._start_time
            ).total_seconds(),
        }
        return self._recorder.finalize_external(
            environment=self.environment,
            task_id=self.task_id,
            parent_run_id=self.parent_run_id,
            agent_name=self.agent_name,
            agent_id=self.agent_id,
            final_response=final_output,
            status=internal_status,
            statistics=statistics,
        )


def _bind_arguments(
    signature: inspect.Signature, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Bind a call's positional/keyword arguments to their parameter names, best-effort."""
    try:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)
    except TypeError:
        return {"args": list(args), "kwargs": kwargs}
