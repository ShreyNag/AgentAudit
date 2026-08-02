"""``ExecutionPlanner`` loop-control logic (PROJECT_SPEC_6 SS41-42)."""

from __future__ import annotations

from app.execution.config import ExecutionConfig
from app.execution.planner import ExecutionPlanner
from app.execution.state import ExecutionState
from app.providers.schemas import ProviderResponse, ToolCallSchema
from app.tools.schemas import ToolInvocationResult


class TestExecutionPlanner:
    def test_needs_tool_execution_true_when_tool_calls_present(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig())
        response = ProviderResponse(
            provider="fake",
            model="fake",
            tool_calls=[ToolCallSchema(id="1", tool_name="flight_search", arguments={})],
        )
        assert planner.needs_tool_execution(response) is True

    def test_needs_tool_execution_false_for_final_answer(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig())
        response = ProviderResponse(provider="fake", model="fake", content="done")
        assert planner.needs_tool_execution(response) is False

    def test_has_reached_limits_on_iteration_count(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig(max_iterations=2))
        state = ExecutionState(iteration_count=2)
        assert planner.has_reached_limits(state) is True

    def test_has_reached_limits_on_tool_call_count(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig(max_tool_calls=1))
        state = ExecutionState(tool_call_count=1)
        assert planner.has_reached_limits(state) is True

    def test_has_not_reached_limits_below_thresholds(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig(max_iterations=5, max_tool_calls=5))
        state = ExecutionState(iteration_count=1, tool_call_count=1)
        assert planner.has_reached_limits(state) is False

    def test_build_tool_result_message_for_success(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig())
        tool_call = ToolCallSchema(id="tc-1", tool_name="flight_search", arguments={})
        result = ToolInvocationResult(
            tool_name="flight_search", arguments={}, output={"flights": []}, status="completed"
        )
        message = planner.build_tool_result_message(tool_call, result)
        assert message.role == "tool"
        assert message.tool_call_id == "tc-1"
        assert "flights" in message.content

    def test_build_tool_result_message_for_failure(self) -> None:
        planner = ExecutionPlanner(ExecutionConfig())
        tool_call = ToolCallSchema(id="tc-1", tool_name="book_flight", arguments={})
        result = ToolInvocationResult(
            tool_name="book_flight", arguments={}, status="failed", error="Unknown flight_id."
        )
        message = planner.build_tool_result_message(tool_call, result)
        assert "error" in message.content
