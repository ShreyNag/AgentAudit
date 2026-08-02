"""In-memory benchmark domain objects (PROJECT_SPEC_1 SS55/SS78).

Distinct from the persisted ORM models in :mod:`app.models` -- these are the objects the
execution engine works with at runtime, before (and independent of) persistence.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single benchmark task, immutable once loaded (PROJECT_SPEC_1 SS55)."""

    task_id: str
    title: str
    description: str
    environment: str
    difficulty: str
    instruction: str
    ground_truth: dict[str, object]
    expected_tool_sequence: list[str] = Field(default_factory=list)
    attack_type: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class BenchmarkEnvironmentMeta(BaseModel):
    """Metadata describing one registered benchmark environment (PROJECT_SPEC_1 SS78)."""

    name: str
    description: str
    version: str = "1.0"
    toolset: list[str] = Field(default_factory=list)
    difficulty_levels: list[str] = Field(default_factory=lambda: ["easy", "medium", "hard"])
    metadata: dict[str, object] = Field(default_factory=dict)
