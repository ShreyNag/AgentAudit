"""Benchmark request/response schemas (PROJECT_SPEC_2 SS94)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkTaskResponse(BaseModel):
    """A single persisted benchmark task. Ground truth is intentionally never exposed here
    (PROJECT_SPEC_1 SS62)."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    title: str
    description: str
    environment: str
    difficulty: str
    attack_type: str | None = None
    instruction: str
    expected_tool_sequence: list[str] = Field(default_factory=list)
    created_at: dt.datetime


class BenchmarkEnvironmentResponse(BaseModel):
    """A registered benchmark environment's public metadata."""

    name: str
    description: str
    version: str = "1.0"
    toolset: list[str] = Field(default_factory=list)
    difficulty_levels: list[str] = Field(default_factory=list)
