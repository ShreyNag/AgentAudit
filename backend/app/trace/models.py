"""In-memory trace domain objects (PROJECT_SPEC_1 SS59-60).

Distinct from the persisted ORM models in :mod:`app.models` -- these are what the Trace
Recorder builds up during execution, before (and independent of) persistence.
"""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field

from app.trace.events import TraceEventType


class TraceEvent(BaseModel):
    """A single, immutable, ordered event within an execution trace (PROJECT_SPEC_1 SS59)."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    timestamp: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))
    event_type: TraceEventType
    component: str
    provider: str | None = None
    model: str | None = None
    input: dict[str, object] = Field(default_factory=dict)
    output: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)
    latency: float | None = None
    status: str = "ok"
    error: str | None = None
    sequence_number: int = 0


class ExecutionTrace(BaseModel):
    """The complete execution trace for one run (PROJECT_SPEC_1 SS60): the single source of
    truth every evaluator consumes."""

    run_uuid: str
    metadata: dict[str, object] = Field(default_factory=dict)
    task: dict[str, object] = Field(default_factory=dict)
    environment: str = ""
    provider: str = ""
    model: str = ""
    planner: dict[str, object] = Field(default_factory=dict)
    messages: list[dict[str, object]] = Field(default_factory=list)
    tool_calls: list[dict[str, object]] = Field(default_factory=list)
    tool_outputs: list[dict[str, object]] = Field(default_factory=list)
    reasoning: dict[str, object] = Field(default_factory=dict)
    reasoning_steps: list[dict[str, object]] = Field(default_factory=list)
    reflection_turns: list[dict[str, object]] = Field(default_factory=list)
    memory: dict[str, object] = Field(default_factory=dict)
    observations: list[dict[str, object]] = Field(default_factory=list)
    environment_changes: list[dict[str, object]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    final_response: str | None = None
    statistics: dict[str, object] = Field(default_factory=dict)
    events: list[TraceEvent] = Field(default_factory=list)
    version: str = "1.0"
