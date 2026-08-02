"""Evaluation Engine (PROJECT_SPEC_3, PROJECT_SPEC_6 Part 3): independent of execution.

Nothing here imports from :mod:`app.execution`, :mod:`app.environments`, or :mod:`app.tools`
(PROJECT_SPEC_1 SS106) -- evaluation consumes only a persisted
:class:`~app.trace.models.ExecutionTrace`.
"""

from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.context import EvaluationContext
from app.evaluation.engine import EvaluationEngine
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.judge import JudgeService
from app.evaluation.models import (
    BehaviourClassificationResult,
    CTSResult,
    EvaluationOutcome,
    EvaluationResult,
    Evidence,
    FailureAttributionResult,
)
from app.evaluation.scoring.cts import CTSCalculator

__all__ = [
    "BehaviourClassifier",
    "EvaluationContext",
    "EvaluationEngine",
    "EvidenceExtractor",
    "FailureAttributionEngine",
    "JudgeService",
    "BehaviourClassificationResult",
    "CTSResult",
    "EvaluationOutcome",
    "EvaluationResult",
    "Evidence",
    "FailureAttributionResult",
    "CTSCalculator",
]
