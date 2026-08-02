"""``TraceRecorder`` (PROJECT_SPEC_2 SS78, PROJECT_SPEC_6 SS51): passive, ordered recording."""

from __future__ import annotations

from app.benchmark.models import Task
from app.execution.result import ExecutionStatistics
from app.providers.schemas import ProviderRequest, ProviderResponse, ToolCallSchema
from app.tools.schemas import ToolInvocationResult
from app.trace.recorder import TraceRecorder


class TestTraceRecorder:
    def test_events_are_sequenced_in_order(self) -> None:
        recorder = TraceRecorder(run_uuid="run-1")
        recorder.record_run_started()
        recorder.record_provider_request(ProviderRequest(provider="fake", model="m", messages=[]))
        recorder.record_run_completed("completed")

        sequence_numbers = [event.sequence_number for event in recorder.events]
        assert sequence_numbers == [1, 2, 3]

    def test_reasoning_defaults_to_unavailable_and_is_never_fabricated(self) -> None:
        recorder = TraceRecorder(run_uuid="run-1")
        task = Task(
            task_id="t-1",
            title="t",
            description="d",
            environment="travel",
            difficulty="easy",
            instruction="do it",
            ground_truth={"x": 1},
        )
        trace = recorder.finalize(
            task=task,
            environment_name="travel",
            provider_name="fake",
            model_name="m",
            final_response="done",
            statistics=ExecutionStatistics(),
        )
        assert trace.reasoning == {"reasoning_available": False}
        assert trace.planner == {"planner_available": False}

    def test_reasoning_is_recorded_when_present(self) -> None:
        recorder = TraceRecorder(run_uuid="run-1")
        response = ProviderResponse(
            provider="fake",
            model="m",
            content="answer",
            reasoning="because X",
            reasoning_available=True,
        )
        recorder.record_reasoning(response)
        assert recorder._reasoning["reasoning_available"] is True
        assert recorder._reasoning["content"] == "because X"

    def test_tool_completed_and_failed_use_distinct_event_types(self) -> None:
        recorder = TraceRecorder(run_uuid="run-1")
        tool_call = ToolCallSchema(id="tc-1", tool_name="book_flight", arguments={})

        recorder.record_tool_completed(
            tool_call,
            ToolInvocationResult(tool_name="book_flight", arguments={}, status="completed"),
        )
        recorder.record_tool_completed(
            tool_call,
            ToolInvocationResult(
                tool_name="book_flight", arguments={}, status="failed", error="boom"
            ),
        )
        event_types = [event.event_type for event in recorder.events]
        assert "ToolCompleted" in event_types
        assert "ToolFailed" in event_types

    def test_errors_are_never_discarded(self) -> None:
        recorder = TraceRecorder(run_uuid="run-1")
        recorder.record_error(RuntimeError("execution blew up"))
        task = Task(
            task_id="t-1",
            title="t",
            description="d",
            environment="travel",
            difficulty="easy",
            instruction="do it",
            ground_truth={"x": 1},
        )
        trace = recorder.finalize(
            task=task,
            environment_name="travel",
            provider_name="fake",
            model_name="m",
            final_response=None,
            statistics=ExecutionStatistics(),
        )
        assert "execution blew up" in trace.errors
