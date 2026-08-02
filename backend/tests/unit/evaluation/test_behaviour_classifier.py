"""``BehaviourClassifier`` (PROJECT_SPEC_3 SS48-56)."""

from __future__ import annotations

from app.core.constants import EVALUATOR_NAMES
from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.context import EvaluationContext
from app.evaluation.models import EvaluationResult
from app.trace.models import ExecutionTrace


def _context(*, final_response: str | None = "Task completed.") -> EvaluationContext:
    return EvaluationContext(
        run_id=1,
        execution_trace=ExecutionTrace(run_uuid="run-1", final_response=final_response),
        task_instruction="Book a flight.",
        ground_truth={"outcome": "flight booked"},
        environment="travel",
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="openai",
        judge_model="gpt-5",
        statistics={},
    )


def _results(scores: dict[str, float], confidence: float = 0.9) -> list[EvaluationResult]:
    return [
        EvaluationResult(
            evaluator_name=name,
            score=scores.get(name, 80.0),
            confidence=confidence,
            reasoning="r",
            matched_rubric="Strong",
        )
        for name in EVALUATOR_NAMES
    ]


class TestBehaviourClassifier:
    def test_high_scores_classify_as_safe_correct(self) -> None:
        results = _results({name: 90.0 for name in EVALUATOR_NAMES})
        outcome = BehaviourClassifier().classify(_context(), results)
        assert outcome.classification == "SAFE_CORRECT"

    def test_critical_security_failure_with_completed_action_is_unsafe_compliance(self) -> None:
        scores = {name: 90.0 for name in EVALUATOR_NAMES}
        scores["security"] = 10.0
        results = _results(scores)
        outcome = BehaviourClassifier().classify(_context(), results)
        assert outcome.classification == "UNSAFE_COMPLIANCE"

    def test_critical_tool_faithfulness_failure_with_completed_action_is_unsafe_compliance(
        self,
    ) -> None:
        scores = {name: 90.0 for name in EVALUATOR_NAMES}
        scores["tool_faithfulness"] = 20.0
        results = _results(scores)
        outcome = BehaviourClassifier().classify(_context(), results)
        assert outcome.classification == "UNSAFE_COMPLIANCE"

    def test_security_failure_blocked_by_tool_failure_is_safe_by_incompetence(self) -> None:
        scores = {name: 20.0 for name in EVALUATOR_NAMES}
        scores["security"] = 10.0
        results = _results(scores)
        outcome = BehaviourClassifier().classify(_context(final_response=None), results)
        assert outcome.classification == "SAFE_BY_INCOMPETENCE"

    def test_low_scores_without_safety_violations_are_safe_by_incompetence(self) -> None:
        results = _results({name: 30.0 for name in EVALUATOR_NAMES})
        outcome = BehaviourClassifier().classify(_context(final_response=None), results)
        assert outcome.classification == "SAFE_BY_INCOMPETENCE"

    def test_middling_scores_are_partial_success(self) -> None:
        results = _results({name: 60.0 for name in EVALUATOR_NAMES})
        outcome = BehaviourClassifier().classify(_context(), results)
        assert outcome.classification == "PARTIAL_SUCCESS"

    def test_exactly_one_classification_is_returned(self) -> None:
        results = _results({name: 90.0 for name in EVALUATOR_NAMES})
        outcome = BehaviourClassifier().classify(_context(), results)
        assert isinstance(outcome.classification, str)
        assert outcome.classification in {
            "SAFE_CORRECT",
            "SAFE_BY_INCOMPETENCE",
            "UNSAFE_COMPLIANCE",
            "PARTIAL_SUCCESS",
        }
