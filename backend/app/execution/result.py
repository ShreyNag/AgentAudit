"""``ExecutionResult`` / ``ExecutionStatistics`` (PROJECT_SPEC_6 SS40/SS58)."""

from __future__ import annotations

from pydantic import BaseModel


class ExecutionStatistics(BaseModel):
    """Automatically computed metrics for one execution (PROJECT_SPEC_1 SS62)."""

    execution_time_seconds: float = 0.0
    planner_iterations: int = 0
    provider_calls: int = 0
    tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ExecutionResult(BaseModel):
    """The outcome of one completed run.

    References persisted artifacts (``run_uuid``) rather than embedding the full trace
    (PROJECT_SPEC_6 SS40) -- the trace itself is retrieved separately via the Trace Layer.
    """

    run_uuid: str
    status: str
    final_response: str | None = None
    statistics: ExecutionStatistics
    error: str | None = None
