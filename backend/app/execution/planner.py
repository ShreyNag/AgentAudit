"""``ExecutionPlanner`` (PROJECT_SPEC_6 SS41-42): the reasoning-loop control logic.

The planner never generates language itself -- that is delegated to the provider adapter
(PROJECT_SPEC_6 SS41). It only decides whether another tool round is needed and guards against
infinite loops.
"""

from __future__ import annotations

import json

from app.execution.config import ExecutionConfig
from app.execution.state import ExecutionState
from app.providers.schemas import ProviderMessage, ProviderResponse, ToolCallSchema
from app.tools.schemas import ToolInvocationResult


class ExecutionPlanner:
    """Decides the next step of the execution loop given the latest provider response."""

    def __init__(self, config: ExecutionConfig) -> None:
        """Bind the planner to the execution's configuration (iteration/tool-call limits)."""
        self.config = config

    def needs_tool_execution(self, response: ProviderResponse) -> bool:
        """Return whether ``response`` requested one or more tool calls."""
        return bool(response.tool_calls)

    def has_reached_limits(self, state: ExecutionState) -> bool:
        """Return whether the run has hit its configured iteration or tool-call ceiling.

        Prevents infinite loops (PROJECT_SPEC_6 SS41).
        """
        return (
            state.iteration_count >= self.config.max_iterations
            or state.tool_call_count >= self.config.max_tool_calls
        )

    def build_tool_result_message(
        self, tool_call: ToolCallSchema, result: ToolInvocationResult
    ) -> ProviderMessage:
        """Build the conversation message that reports a tool's outcome back to the model."""
        content = (
            json.dumps(result.output)
            if result.status == "completed"
            else json.dumps({"error": result.error})
        )
        return ProviderMessage(
            role="tool", content=content, tool_call_id=tool_call.id, name=tool_call.tool_name
        )
