"""``TraceRecorder`` (PROJECT_SPEC_2 SS78, PROJECT_SPEC_6 SS51): passively records execution.

Never modifies execution behavior, never writes directly to the database (PROJECT_SPEC_6
SS51/SS72's persistence workflow persists the finalized trace separately, via
:mod:`app.repositories`). Reasoning/planning are recorded only when actually present -- never
fabricated (PROJECT_SPEC_1 SS52/SS63).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.benchmark.models import Task
from app.providers.schemas import ProviderRequest, ProviderResponse, ToolCallSchema
from app.tools.schemas import ToolInvocationResult
from app.trace.events import TraceEventType
from app.trace.models import ExecutionTrace, TraceEvent

if TYPE_CHECKING:
    from app.execution.result import ExecutionStatistics


class TraceRecorder:
    """Accumulates trace events for a single run, in order, without persisting them."""

    def __init__(self, run_uuid: str) -> None:
        """Start an empty trace for ``run_uuid``."""
        self.run_uuid = run_uuid
        self._events: list[TraceEvent] = []
        self._sequence = 0
        self._messages: list[dict[str, Any]] = []
        self._tool_calls: list[dict[str, Any]] = []
        self._tool_outputs: list[dict[str, Any]] = []
        self._errors: list[str] = []
        self._reasoning: dict[str, Any] = {"reasoning_available": False}
        self._reasoning_steps: list[dict[str, Any]] = []
        self._reflection_turns: list[dict[str, Any]] = []
        self._planner: dict[str, Any] = {"planner_available": False}

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def _append(
        self,
        event_type: TraceEventType,
        *,
        component: str,
        provider: str | None = None,
        model: str | None = None,
        input: dict[str, Any] | None = None,  # noqa: A002 - matches PROJECT_SPEC_1 SS59 field name
        output: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        latency: float | None = None,
        status: str = "ok",
        error: str | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            execution_id=self.run_uuid,
            event_type=event_type,
            component=component,
            provider=provider,
            model=model,
            input=input or {},
            output=output or {},
            metadata=metadata or {},
            latency=latency,
            status=status,
            error=error,
            sequence_number=self._next_sequence(),
        )
        self._events.append(event)
        return event

    def record_run_started(self) -> None:
        """Record the ``RunStarted`` event."""
        self._append(TraceEventType.RUN_STARTED, component="runner")

    def record_provider_request(self, request: ProviderRequest) -> None:
        """Record the outgoing normalized provider request."""
        self._append(
            TraceEventType.PROVIDER_REQUEST,
            component="provider",
            provider=request.provider,
            model=request.model,
            input=request.model_dump(mode="json"),
        )

    def record_provider_response(self, response: ProviderResponse) -> None:
        """Record the normalized provider response and append it to conversation history."""
        self._append(
            TraceEventType.PROVIDER_RESPONSE,
            component="provider",
            provider=response.provider,
            model=response.model,
            output=response.model_dump(mode="json"),
            latency=response.latency,
        )
        self._messages.append(
            {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [tc.model_dump(mode="json") for tc in response.tool_calls],
            }
        )

    def record_reasoning(self, response: ProviderResponse) -> None:
        """Record the model's stated reasoning for this turn.

        Prefers the provider's dedicated extended-thinking channel (``response.reasoning``) when
        present; otherwise falls back to its regular response content, which is where most
        providers' brief before-action explanations actually appear (PROJECT_SPEC_1 SS62's system
        prompt asks the model to state its reasoning there before every tool call and final
        answer). Called once per turn, so every step of the run's reasoning is captured in order,
        not just the final one -- never fabricated, only recorded when the model actually said
        something (PROJECT_SPEC_1 SS52/SS63).
        """
        content = (
            response.reasoning
            if response.reasoning_available and response.reasoning
            else response.content
        )
        self._reasoning = {"reasoning_available": bool(content), "content": content}
        self._reasoning_steps.append(dict(self._reasoning))
        self._append(
            TraceEventType.REASONING_GENERATED,
            component="planner",
            output=dict(self._reasoning),
        )

    def record_tool_selected(self, tool_call: ToolCallSchema) -> None:
        """Record that the model requested ``tool_call``."""
        self._append(
            TraceEventType.TOOL_SELECTED,
            component="tool_registry",
            input=tool_call.model_dump(mode="json"),
        )

    def record_tool_completed(
        self, tool_call: ToolCallSchema, result: ToolInvocationResult
    ) -> None:
        """Record the outcome of one tool invocation, successful or not."""
        event_type = (
            TraceEventType.TOOL_COMPLETED
            if result.status == "completed"
            else TraceEventType.TOOL_FAILED
        )
        self._append(
            event_type,
            component="tool_registry",
            input=tool_call.model_dump(mode="json"),
            output=result.model_dump(mode="json"),
            latency=result.latency,
            status=result.status,
            error=result.error,
        )
        self._tool_calls.append(
            {
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "status": result.status,
                "latency": result.latency,
            }
        )
        self._tool_outputs.append(
            {"tool_name": tool_call.tool_name, "output": result.output, "error": result.error}
        )

    def record_reflection(self, probe: str, response: str | None) -> None:
        """Record one post-task reflection exchange (probe + the model's response).

        Kept out of ``reasoning_steps``/``final_response`` deliberately: the reflection turn is
        evidence for the Alignment evaluator only, and must never be mistaken for (or overwrite)
        the task's actual final answer, which Tool Correctness/Faithfulness still need intact.
        """
        entry = {"probe": probe, "response": response}
        self._reflection_turns.append(entry)
        self._append(TraceEventType.REFLECTION_RECORDED, component="executor", output=entry)

    def record_warning(self, message: str) -> None:
        """Record a non-fatal warning (e.g. an execution limit was reached)."""
        self._append(TraceEventType.WARNING, component="executor", status="warning", error=message)

    def record_error(self, exc: Exception) -> None:
        """Record an execution error. Errors are never discarded (PROJECT_SPEC_1 SS66)."""
        self._errors.append(str(exc))
        self._append(TraceEventType.ERROR, component="executor", status="error", error=str(exc))

    def record_run_completed(self, status: str) -> None:
        """Record the terminal event for this run."""
        event_type = (
            TraceEventType.RUN_COMPLETED if status == "completed" else TraceEventType.RUN_FAILED
        )
        self._append(event_type, component="runner", status=status)

    @property
    def events(self) -> list[TraceEvent]:
        """Return every recorded event, in order."""
        return list(self._events)

    def finalize(
        self,
        *,
        task: Task,
        environment_name: str,
        provider_name: str,
        model_name: str,
        final_response: str | None,
        statistics: ExecutionStatistics,
    ) -> ExecutionTrace:
        """Assemble every recorded event and side-channel into one immutable

        :class:`ExecutionTrace`.
        """
        return ExecutionTrace(
            run_uuid=self.run_uuid,
            metadata={"event_count": len(self._events), "task_id": task.task_id},
            task=task.model_dump(mode="json"),
            environment=environment_name,
            provider=provider_name,
            model=model_name,
            planner=dict(self._planner),
            messages=list(self._messages),
            tool_calls=list(self._tool_calls),
            tool_outputs=list(self._tool_outputs),
            reasoning=dict(self._reasoning),
            reasoning_steps=list(self._reasoning_steps),
            reflection_turns=list(self._reflection_turns),
            memory={},
            observations=[],
            environment_changes=[],
            errors=list(self._errors),
            final_response=final_response,
            statistics=statistics.model_dump(mode="json"),
            events=list(self._events),
        )
