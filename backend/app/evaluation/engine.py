"""``EvaluationEngine`` (PROJECT_SPEC_3 SS7, PROJECT_SPEC_6 SS64): orchestrates evaluation only.

The engine implements no evaluator-specific logic itself (PROJECT_SPEC_6 SS64) and performs no
scoring (PROJECT_SPEC_3 SS7) -- it only sequences the independent stages and hands their outputs
to the next.
"""

from __future__ import annotations

from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.context import EvaluationContext
from app.evaluation.evaluators.registry import EvaluatorRegistry
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.judge import JudgeService
from app.evaluation.models import EvaluationOutcome
from app.evaluation.rubric.loader import RubricLoader
from app.evaluation.scoring.cts import CTSCalculator


class EvaluationEngine:
    """Coordinates evaluators, behaviour classification, failure attribution, and CTS."""

    def __init__(
        self,
        evaluator_registry: EvaluatorRegistry,
        behaviour_classifier: BehaviourClassifier,
        failure_attribution: FailureAttributionEngine,
        cts_calculator: CTSCalculator,
        evidence_extractor: EvidenceExtractor,
        rubric_loader: RubricLoader,
    ) -> None:
        """Bind the engine to every stage of the evaluation pipeline."""
        self._evaluator_registry = evaluator_registry
        self._behaviour_classifier = behaviour_classifier
        self._failure_attribution = failure_attribution
        self._cts_calculator = cts_calculator
        self._evidence_extractor = evidence_extractor
        self._rubric_loader = rubric_loader

    async def run(self, context: EvaluationContext, judge: JudgeService) -> EvaluationOutcome:
        """Run the full evaluation lifecycle for ``context`` and return the complete outcome."""
        results = await self._evaluator_registry.run_all(
            context,
            judge=judge,
            evidence_extractor=self._evidence_extractor,
            rubric_loader=self._rubric_loader,
        )
        behaviour = self._behaviour_classifier.classify(context, results)
        failure = self._failure_attribution.analyze(context, results)
        cts = self._cts_calculator.compute(
            results,
            behaviour=behaviour.classification,
            primary_failure=failure.primary_failure if failure else None,
        )
        return EvaluationOutcome(
            evaluator_results=results, behaviour=behaviour, failure=failure, cts=cts
        )
