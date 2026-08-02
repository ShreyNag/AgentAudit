"""``ExecutionConfig`` (PROJECT_SPEC_6 SS39): immutable for the duration of a run."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExecutionConfig(BaseModel):
    """Execution-loop configuration for a single run."""

    model_config = ConfigDict(frozen=True)

    max_iterations: int = 10
    max_tool_calls: int = 20
    timeout_seconds: float = 120.0
    max_retries: int = 3
    temperature: float = 0.7
    # 4096 was tight given the system prompt asks for a reasoning sentence before every tool
    # call plus the full message history resent each turn; a response truncated mid-turn can
    # leave a dangling/incomplete tool_use block that a later turn's request then fails on.
    max_tokens: int = 8192
    streaming_enabled: bool = False
