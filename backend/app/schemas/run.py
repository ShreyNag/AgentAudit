"""Run request/response schemas (PROJECT_SPEC_2 SS94-95)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class RunLaunchRequest(BaseModel):
    """Request body for ``POST /api/v1/benchmarks/run``."""

    task_id: str
    provider: str | None = None
    model: str | None = None


class RunResponse(BaseModel):
    """A single benchmark run (PROJECT_SPEC_1 SS80)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    run_uuid: str
    benchmark_task_id: int
    provider: str
    model: str
    judge_provider: str | None = None
    judge_model: str | None = None
    environment: str
    status: str
    execution_time: float | None = None
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
    created_at: dt.datetime
