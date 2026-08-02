"""``FailureAttributionEngine`` (PROJECT_SPEC_3 SS57-62)."""

from __future__ import annotations

from app.core.constants import EVALUATOR_NAMES
from app.evaluation.context import EvaluationContext
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.models import EvaluationResult, Evidence
from app.trace.models import ExecutionTrace


def _context() -> EvaluationContext:
    return EvaluationContext(
        run_id=1,
        execution_trace=ExecutionTrace(run_uuid="run-1"),
        task_instruction="Book a flight.",
        ground_truth={},
        environment="travel",
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="openai",
        judge_model="gpt-5",
        statistics={},
    )


def _results(scores: dict[str, float]) -> list[EvaluationResult]:
    return [
        EvaluationResult(
            evaluator_name=name,
            score=scores.get(name, 90.0),
            confidence=0.85,
            reasoning=f"{name} reasoning",
            weaknesses=[f"{name} weakness"] if scores.get(name, 90.0) < 50.0 else [],
            evidence=[Evidence(evidence_id="e1", category=name, description="evidence")],
            matched_rubric="Weak" if scores.get(name, 90.0) < 50.0 else "Strong",
        )
        for name in EVALUATOR_NAMES
    ]


class TestFailureAttributionEngine:
    def test_no_failure_when_all_scores_are_high(self) -> None:
        results = _results({name: 90.0 for name in EVALUATOR_NAMES})
        assert FailureAttributionEngine().analyze(_context(), results) is None

    def test_lowest_scoring_evaluator_is_primary_failure(self) -> None:
        results = _results({"tool_selection": 20.0, "tool_invocation": 30.0})
        attribution = FailureAttributionEngine().analyze(_context(), results)
        assert attribution is not None
        assert attribution.primary_failure == "tool_selection"
        assert "tool_invocation" in attribution.secondary_failures

    def test_secondary_failures_capped_at_three(self) -> None:
        results = _results(
            {
                "tool_selection": 10.0,
                "tool_invocation": 20.0,
                "memory": 25.0,
                "planner": 30.0,
                "alignment": 40.0,
            }
        )
        attribution = FailureAttributionEngine().analyze(_context(), results)
        assert attribution is not None
        assert len(attribution.secondary_failures) <= 3

    def test_empty_results_returns_none(self) -> None:
        assert FailureAttributionEngine().analyze(_context(), []) is None
