"""Trace request/response schemas (PROJECT_SPEC_2 SS96)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class TraceResponse(BaseModel):
    """The persisted execution trace document for one run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: int
    planner: dict[str, object] = Field(default_factory=dict)
    reasoning: dict[str, object] = Field(default_factory=dict)
    messages: list[dict[str, object]] = Field(default_factory=list)
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
