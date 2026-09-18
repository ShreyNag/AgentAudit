"""Evaluation domain objects.

PROJECT_SPEC_3 SS11/SS16/SS41/SS65, PROJECT_SPEC_6 SS70/SS72/SS80/SS82/SS84.

All evaluation is independent from execution: nothing in this module imports from
:mod:`app.execution` or :mod:`app.environments` (PROJECT_SPEC_1 SS106).
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """One immutable, traceable piece of evidence supporting an evaluator's conclusion.

    Merges PROJECT_SPEC_3 SS16/SS65 and PROJECT_SPEC_6 SS72's evidence object definitions.
    """

    evidence_id: str
    trace_event_id: str | None = None
    category: str
    description: str
    severity: str = "info"
    supporting_data: dict[str, object] = Field(default_factory=dict)
    timestamp: dt.datetime | None = None


class CriterionAssessment(BaseModel):
    """One rubric criterion's verdict within a single evaluator judgment (PROJECT_SPEC_3 SS13).

    Lets a reviewer see *why* a score landed where it did, criterion by criterion, rather than
    only the aggregate score and a free-text summary.
    """

    criterion: str
    status: str  # "followed" | "partially_followed" | "ignored"
    justification: str = ""


class EvaluationResult(BaseModel):
    """The standardized output of a single evaluator (PROJECT_SPEC_3 SS41, PROJECT_SPEC_6 SS70).

    ``score`` is on a 0-100 scale; ``confidence`` is 0.0-1.0 (PROJECT_SPEC_3 SS18), reported
    independently from score.
    """

    evaluator_name: str
    score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    expected_outcome: str = ""
    actual_outcome: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    matched_rubric: str = "unknown"
    criteria_assessment: list[CriterionAssessment] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    execution_time: float = 0.0


class BehaviourClassificationResult(BaseModel):
    """One primary behavioural classification for a run (PROJECT_SPEC_3 SS48-56)."""

    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    supporting_evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class FailureAttributionResult(BaseModel):
    """The primary and secondary causes of execution failure (PROJECT_SPEC_3 SS57-62)."""

    primary_failure: str
    secondary_failures: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    affected_components: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)


class CTSResult(BaseModel):
    """The Composite Trust Score and its full supporting context (PROJECT_SPEC_3 SS96).

    The critical-failure cap (PROJECT_SPEC_3 SS85-86) is a deployment policy layered on top of
    the metric, not part of the metric itself (docs/adr/0008-cts-cap-is-policy-not-metric.md):
    ``cts_raw`` is the uncapped weighted sum and is what every analysis/aggregation/comparison
    across runs must use; ``cts_reported`` is ``cts_raw`` clamped to 30 when a hard-cap evaluator
    critically failed, and is what deploy/no-deploy decisions and the primary UI display use.
    """

    cts_raw: float = Field(ge=0.0, le=100.0)
    cts_reported: float = Field(ge=0.0, le=100.0)
    trust_level: str
    confidence: float = Field(ge=0.0, le=1.0)
    weight_version: str = "1.0"
    behaviour: str | None = None
    primary_failure: str | None = None
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    evaluator_contributions: dict[str, float] = Field(default_factory=dict)
    critical_failure: bool = False
    critical_failure_modules: list[str] = Field(default_factory=list)


class EvaluationOutcome(BaseModel):
    """The complete output of one evaluation run: every stage's result, bundled together."""

    evaluator_results: list[EvaluationResult]
    behaviour: BehaviourClassificationResult
    failure: FailureAttributionResult | None
    cts: CTSResult
