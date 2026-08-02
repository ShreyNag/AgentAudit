"""Execution Engine (PROJECT_SPEC_6 Part 2): runs the Agent Under Test, never evaluates it.

Only :class:`~app.execution.runner.ExecutionRunner` is meant to be called from the service
layer; every other class here exists to support it.
"""

from app.execution.common_agent_executor import CommonAgentExecutor
from app.execution.config import ExecutionConfig
from app.execution.context import ExecutionContext
from app.execution.planner import ExecutionPlanner
from app.execution.result import ExecutionResult, ExecutionStatistics
from app.execution.runner import ExecutionRunner
from app.execution.state import ExecutionState

__all__ = [
    "CommonAgentExecutor",
    "ExecutionConfig",
    "ExecutionContext",
    "ExecutionPlanner",
    "ExecutionResult",
    "ExecutionStatistics",
    "ExecutionRunner",
    "ExecutionState",
]
