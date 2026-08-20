"""Trace request/response schemas (PROJECT_SPEC_2 SS96)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class TraceResponse(BaseModel):
    """The persisted execution trace document for one run."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    run_id: int
    planner: dict[str, object] = Field(default_factory=dict)
    reasoning: dict[str, object] = Field(default_factory=dict)
    messages: list[dict[str, object]] = Field(default_factory=list)
    # The ORM attribute is ``trace_metadata`` (the DB column itself is named "metadata", per
    # app.models.execution_trace.ExecutionTraceModel) -- aliased so the API surfaces the same
    # name ExecutionTrace.metadata uses everywhere else. Carries agent_name/agent_id/task_id/
    # parent_run_id/source for a run observed via AgentAuditTracer (see finalize_external()).
    metadata: dict[str, object] = Field(default_factory=dict, validation_alias="trace_metadata")
    statistics: dict[str, object] = Field(default_factory=dict)
    version: str
    created_at: dt.datetime


class TraceEventResponse(BaseModel):
    """A single event on the execution timeline."""

    model_config = ConfigDict(from_attributes=True)

    event_number: int
    timestamp: dt.datetime
    event_type: str
    component: str
    payload: dict[str, object] = Field(default_factory=dict)
    latency: float | None = None
    status: str
