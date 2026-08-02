"""Dashboard response schemas (PROJECT_SPEC_2 SS99)."""

from __future__ import annotations

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    """Top-line dashboard statistics."""

    total_runs: int
    completed_runs: int
    failed_runs: int
    running_runs: int
    average_cts: float | None = None


class GroupedCountResponse(BaseModel):
    """One group's row count (e.g. one provider's, or one environment's)."""

    label: str
    count: int


class EvaluatorStatisticResponse(BaseModel):
    """Aggregate statistics for a single evaluator across every evaluated run."""

    evaluator_name: str
    average_score: float
    average_confidence: float
    count: int
