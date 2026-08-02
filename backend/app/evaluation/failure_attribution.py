"""``FailureAttributionEngine`` (PROJECT_SPEC_3 SS57-62, PROJECT_SPEC_6 SS81-82).

Identifies the primary and secondary causes of execution failure from the ten evaluators'
already-computed results -- it never re-examines the trace directly (PROJECT_SPEC_3 SS55: "No
raw provider responses are required").
"""

from __future__ import annotations

from app.evaluation.context import EvaluationContext
from app.evaluation.models import EvaluationResult, FailureAttributionResult

#: An evaluator scoring below "Acceptable" (PROJECT_SPEC_3 SS42) is considered a contributing
#: failure; below this, execution did not meet its core criteria for that dimension.
_FAILURE_THRESHOLD = 50.0
#: At most this many additional low scorers are reported as secondary failures
#: (PROJECT_SPEC_3 SS61).
_MAX_SECONDARY_FAILURES = 3


class FailureAttributionEngine:
    """Ranks evaluator weaknesses into a primary cause plus secondary/downstream causes."""

    def analyze(
        self, context: EvaluationContext, results: list[EvaluationResult]
    ) -> FailureAttributionResult | None:
        """Return failure attribution for the lowest-scoring evaluators, or ``None`` if none failed."""  # noqa: E501
        if not results:
            return None

        ranked = sorted(results, key=lambda result: result.score)
        primary = ranked[0]
        if primary.score >= _FAILURE_THRESHOLD:
            return None  # no evaluator fell below the Acceptable threshold -- nothing to attribute

        secondary_candidates = [r for r in ranked[1:] if r.score < _FAILURE_THRESHOLD]
        secondary = [r.evaluator_name for r in secondary_candidates[:_MAX_SECONDARY_FAILURES]]
        affected_components = [primary.evaluator_name, *secondary]

        weakness_summary = (
            "; ".join(primary.weaknesses) if primary.weaknesses else primary.reasoning
        )
        reasoning = (
            f"'{primary.evaluator_name}' scored lowest at {primary.score:.1f} "
            f"({primary.matched_rubric}), driven by: {weakness_summary}"
        )
        supporting_evidence = [item.description for item in primary.evidence[:5]]

        return FailureAttributionResult(
            primary_failure=primary.evaluator_name,
            secondary_failures=secondary,
            confidence=primary.confidence,
            reasoning=reasoning,
            affected_components=affected_components,
            supporting_evidence=supporting_evidence,
        )
