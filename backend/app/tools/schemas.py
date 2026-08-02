"""Tool invocation result schema (PROJECT_SPEC_1 SS54, PROJECT_SPEC_2 SS67)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolInvocationResult(BaseModel):
    """The outcome of one tool invocation, ready for the Trace Recorder to log."""

    tool_name: str
    arguments: dict[str, object]
    validated_arguments: dict[str, object] = Field(default_factory=dict)
    output: dict[str, object] = Field(default_factory=dict)
    status: str = "completed"
    error: str | None = None
    latency: float = 0.0
