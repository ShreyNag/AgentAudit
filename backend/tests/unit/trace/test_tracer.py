"""``AgentAuditTracer``: observing an externally running agent produces a compatible trace."""

from __future__ import annotations

import pytest

from app.trace.events import TraceEventType
from app.trace.tracer import AgentAuditTracer


class TestAgentAuditTracer:
    def test_start_run_generates_a_run_id_and_records_run_started(self) -> None:
        tracer = AgentAuditTracer.start_run(task_id="trip_planner-001")

        assert tracer.run_id
        assert tracer.task_id == "trip_planner-001"
        trace = tracer.finish(final_output="done", status="success")
        event_types = [event.event_type for event in trace.events]
        assert event_types[0] == TraceEventType.RUN_STARTED

    def test_record_llm_call_appends_message_and_provider_events(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_llm_call(model="gpt-5", input="hello", output="hi there")
        trace = tracer.finish(final_output="hi there")

        assert trace.messages == [{"role": "assistant", "content": "hi there", "tool_calls": []}]
        event_types = [event.event_type for event in trace.events]
        assert TraceEventType.PROVIDER_REQUEST in event_types
        assert TraceEventType.PROVIDER_RESPONSE in event_types

    def test_record_llm_call_reasoning_is_never_inferred_from_output(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_llm_call(model="gpt-5", input="hello", output="hi there")
        trace = tracer.finish()

        assert trace.reasoning == {"reasoning_available": False, "content": None}

    def test_record_llm_call_records_explicit_reasoning(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_llm_call(
            model="gpt-5", input="hello", output="hi there", reasoning="Greeting the user."
        )
        trace = tracer.finish()

        assert trace.reasoning == {
            "reasoning_available": True,
            "content": "Greeting the user.",
        }

    def test_record_tool_call_appends_matched_tool_call_and_output(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_tool_call(
            tool_name="search", input={"query": "mumbai"}, output={"results": []}
        )
        trace = tracer.finish()

        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0]["tool_name"] == "search"
        assert trace.tool_calls[0]["status"] == "completed"
        assert len(trace.tool_outputs) == 1
        assert trace.tool_outputs[0]["output"] == {"results": []}
        event_types = [event.event_type for event in trace.events]
        assert TraceEventType.TOOL_SELECTED in event_types
        assert TraceEventType.TOOL_COMPLETED in event_types

    def test_record_tool_call_error_marks_tool_failed_and_records_error(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_tool_call(
            tool_name="search", input={"query": "mumbai"}, error="connection refused"
        )
        trace = tracer.finish(status="error")

        assert trace.tool_calls[0]["status"] == "failed"
        assert trace.tool_outputs[0]["error"] == "connection refused"
        assert "connection refused" in trace.errors
        event_types = [event.event_type for event in trace.events]
        assert TraceEventType.TOOL_FAILED in event_types
        assert trace.final_response is None

    def test_multiple_sequential_events_are_recorded_in_order(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.record_llm_call(model="gpt-5", input="plan", output="I'll search first.")
        tracer.record_tool_call(tool_name="search", input={"q": "x"}, output={"ok": True})
        tracer.record_event(step_type="memory_read", name="recall_preferences")
        tracer.record_llm_call(model="gpt-5", input="summarize", output="Done.")
        trace = tracer.finish(final_output="Done.")

        sequence_numbers = [event.sequence_number for event in trace.events]
        assert sequence_numbers == sorted(sequence_numbers)
        event_types = [event.event_type for event in trace.events]
        assert TraceEventType.AGENT_STEP in event_types

    def test_finish_completes_the_run_and_sets_final_response(self) -> None:
        tracer = AgentAuditTracer.start_run()
        trace = tracer.finish(final_output="the answer", status="success")

        assert trace.final_response == "the answer"
        assert trace.events[-1].event_type == TraceEventType.RUN_COMPLETED

    def test_finish_maps_error_status_to_run_failed(self) -> None:
        tracer = AgentAuditTracer.start_run()
        trace = tracer.finish(final_output=None, status="error")

        assert trace.events[-1].event_type == TraceEventType.RUN_FAILED

    def test_finish_twice_raises(self) -> None:
        tracer = AgentAuditTracer.start_run()
        tracer.finish()
        with pytest.raises(RuntimeError):
            tracer.finish()

    def test_trace_tool_decorator_records_proposal_and_success(self) -> None:
        tracer = AgentAuditTracer.start_run()

        @tracer.trace_tool()
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5
        trace = tracer.finish()

        assert trace.tool_calls[0]["tool_name"] == "add"
        assert trace.tool_calls[0]["arguments"] == {"a": 2, "b": 3}
        assert trace.tool_outputs[0]["output"] == 5

    def test_trace_tool_decorator_records_and_reraises_errors(self) -> None:
        tracer = AgentAuditTracer.start_run()

        @tracer.trace_tool(name="divide")
        def divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(ZeroDivisionError):
            divide(1, 0)
        trace = tracer.finish(status="error")

        assert trace.tool_calls[0]["tool_name"] == "divide"
        assert trace.tool_calls[0]["status"] == "failed"
        assert trace.tool_outputs[0]["error"]

    @pytest.mark.asyncio
    async def test_trace_tool_decorator_supports_async_callables(self) -> None:
        tracer = AgentAuditTracer.start_run()

        @tracer.trace_tool()
        async def lookup(key: str) -> str:
            return f"value-for-{key}"

        result = await lookup(key="x")
        assert result == "value-for-x"
        trace = tracer.finish()
        assert trace.tool_calls[0]["tool_name"] == "lookup"
        assert trace.tool_outputs[0]["output"] == "value-for-x"

    def test_best_effort_mode_swallows_recording_failures(self) -> None:
        tracer = AgentAuditTracer.start_run(mode="best_effort")

        def _boom() -> None:
            raise RuntimeError("simulated recorder failure")

        tracer._guard("record_llm_call", _boom)  # noqa: SLF001 - exercising the guard directly
        # The agent keeps running; finish() still succeeds.
        trace = tracer.finish(final_output="still finished")
        assert trace.final_response == "still finished"

    def test_strict_mode_reraises_recording_failures(self) -> None:
        tracer = AgentAuditTracer.start_run(mode="strict")

        def _boom() -> None:
            raise RuntimeError("simulated recorder failure")

        with pytest.raises(RuntimeError, match="simulated recorder failure"):
            tracer._guard("record_llm_call", _boom)  # noqa: SLF001

    def test_finalize_external_trace_has_no_internal_task_dependency(self) -> None:
        tracer = AgentAuditTracer.start_run(task_id="trip_planner-001", parent_run_id="parent-1")
        trace = tracer.finish(final_output="ok")

        assert trace.task == {}
        assert trace.metadata["task_id"] == "trip_planner-001"
        assert trace.metadata["parent_run_id"] == "parent-1"
        assert trace.metadata["source"] == "external_agent"

    def test_agent_name_and_agent_id_are_recorded_in_trace_metadata(self) -> None:
        tracer = AgentAuditTracer.start_run(agent_name="support-bot", agent_id="v2")
        trace = tracer.finish(final_output="ok")

        assert trace.metadata["agent_name"] == "support-bot"
        assert trace.metadata["agent_id"] == "v2"

    def test_agent_name_and_agent_id_are_omitted_when_not_given(self) -> None:
        tracer = AgentAuditTracer.start_run()
        trace = tracer.finish(final_output="ok")

        assert "agent_name" not in trace.metadata
        assert "agent_id" not in trace.metadata
