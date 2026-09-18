"""Evaluation request/response schemas (PROJECT_SPEC_2 SS97)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class CriterionAssessmentResponse(BaseModel):
    """One rubric criterion's followed/partially_followed/ignored verdict."""

    criterion: str
    status: str
    justification: str = ""


class EvaluationScoreResponse(BaseModel):
    """One evaluator's persisted result."""

    model_config = ConfigDict(from_attributes=True)

    evaluator_name: str
    score: float
    confidence: float
    reasoning: str
    expected_outcome: str = ""
    actual_outcome: str = ""
    evidence: list[dict[str, object]] = Field(default_factory=list)
    rubric_level: str
    matched_criteria: list[str] = Field(default_factory=list)
    criteria_assessment: list[CriterionAssessmentResponse] = Field(default_factory=list)
    created_at: dt.datetime


class EvaluationReportResponse(BaseModel):
    """The persisted composite evaluation report for one run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: int
    overall_reasoning: str
    overall_summary: str
    cts_raw: float
    cts_reported: float
    critical_failure: bool
    critical_failure_modules: list[str] = Field(default_factory=list)
    planner_summary: str | None = None
    security_summary: str | None = None
    integrity_summary: str | None = None
    created_at: dt.datetime


class BehaviourReportResponse(BaseModel):
    """The persisted behavioural classification for one run."""

    model_config = ConfigDict(from_attributes=True)

    classification: str
    confidence: float
    reasoning: str
    evidence: list[str] = Field(default_factory=list)
    created_at: dt.datetime


class FailureReportResponse(BaseModel):
    """The persisted failure attribution for one run."""

    model_config = ConfigDict(from_attributes=True)

    primary_failure: str
    secondary_failures: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    diagnostic_reasoning: str
    confidence: float
    created_at: dt.datetime


class CTSResponse(BaseModel):
    """The Composite Trust Score for one run, with its derived qualitative trust level.

    ``cts_reported`` (clamped) is the decision number for deploy/no-deploy display;
    ``cts_raw`` (uncapped) is the analysis number for aggregation/comparison across runs -- see
    docs/adr/0008-cts-cap-is-policy-not-metric.md.
    """

    run_id: int
    cts_raw: float
    cts_reported: float
    trust_level: str
    critical_failure: bool
    critical_failure_modules: list[str] = Field(default_factory=list)


class RubricLevelResponse(BaseModel):
    """One of a rubric's five performance bands."""

    model_config = ConfigDict(from_attributes=True)

    level: int
    name: str
    min_score: float
    max_score: float
    description: str


class RubricResponse(BaseModel):
    """One evaluator's versioned scoring rubric -- static reference data, not run-specific."""

    model_config = ConfigDict(from_attributes=True)

    identifier: str
    description: str
    criteria: list[str]
    levels: list[RubricLevelResponse]
    failure_conditions: list[str] = Field(default_factory=list)
