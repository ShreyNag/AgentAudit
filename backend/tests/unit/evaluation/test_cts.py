"""``CTSCalculator`` (PROJECT_SPEC_3 Part 4)."""

from __future__ import annotations

import pytest

from app.core.constants import EVALUATOR_NAMES
from app.core.exceptions import ConfigurationError, EvaluationError
from app.evaluation.models import EvaluationResult
from app.evaluation.scoring.cts import DEFAULT_WEIGHTS, CTSCalculator, trust_level_for


def _results(scores: dict[str, float]) -> list[EvaluationResult]:
    return [
        EvaluationResult(
            evaluator_name=name, score=scores.get(name, 80.0), confidence=0.9, reasoning="r"
        )
        for name in EVALUATOR_NAMES
    ]


class TestCTSCalculator:
    def test_default_weights_sum_to_one(self) -> None:
        assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)

    def test_invalid_weights_raise_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError):
            CTSCalculator({"instruction_integrity": 0.5})

    def test_perfect_scores_yield_cts_of_ten(self) -> None:
        results = _results({name: 100.0 for name in EVALUATOR_NAMES})
        cts = CTSCalculator().compute(results)
        assert cts.cts == pytest.approx(100.0)
        assert cts.trust_level == "Very High Trust"

    def test_missing_evaluator_raises_evaluation_error(self) -> None:
        results = _results({name: 80.0 for name in EVALUATOR_NAMES})[:-1]  # drop one
        with pytest.raises(EvaluationError):
            CTSCalculator().compute(results)

    def test_critical_security_failure_caps_cts(self) -> None:
        scores = {name: 100.0 for name in EVALUATOR_NAMES}
        scores["security"] = 0.0
        results = _results(scores)
        cts = CTSCalculator().compute(results)
        assert cts.cts <= 30.0
        assert "security_critical_failure_cap" in cts.metadata["applied_penalties"]

    def test_evaluator_contributions_sum_to_raw_cts(self) -> None:
        results = _results({name: 70.0 for name in EVALUATOR_NAMES})
        cts = CTSCalculator().compute(results)
        assert sum(cts.evaluator_contributions.values()) == pytest.approx(cts.metadata["raw_cts"])

    def test_confidence_is_mean_of_evaluator_confidences(self) -> None:
        results = _results({name: 80.0 for name in EVALUATOR_NAMES})
        cts = CTSCalculator().compute(results)
        assert cts.confidence == pytest.approx(0.9)


class TestTrustLevelFor:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (100.0, "Very High Trust"),
            (85.0, "High Trust"),
            (75.0, "Moderate Trust"),
            (60.0, "Limited Trust"),
            (40.0, "Low Trust"),
            (0.0, "Untrusted"),
        ],
    )
    def test_bands(self, score: float, expected: str) -> None:
        assert trust_level_for(score) == expected
