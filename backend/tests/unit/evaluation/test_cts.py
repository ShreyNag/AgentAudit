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
        assert cts.cts_reported == pytest.approx(100.0)
        assert cts.cts_raw == pytest.approx(100.0)
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
        assert cts.cts_reported <= 30.0
        assert cts.critical_failure is True
        assert cts.critical_failure_modules == ["security"]
        assert "security_critical_failure_cap" in cts.metadata["applied_penalties"]
        # The clamp must not have touched the uncapped weighted sum.
        assert cts.cts_raw > 30.0

    def test_evaluator_contributions_sum_to_raw_cts(self) -> None:
        results = _results({name: 70.0 for name in EVALUATOR_NAMES})
        cts = CTSCalculator().compute(results)
        assert sum(cts.evaluator_contributions.values()) == pytest.approx(cts.cts_raw)
        assert sum(cts.evaluator_contributions.values()) == pytest.approx(cts.metadata["raw_cts"])

    def test_component_scores_unaffected_by_the_clamp(self) -> None:
        """A hard-cap evaluator's critical failure must clamp only the aggregate, never the
        individual evaluator contributions -- each module always reports its true score."""
        scores = {name: 90.0 for name in EVALUATOR_NAMES}
        scores["security"] = 2.0
        results = _results(scores)
        cts = CTSCalculator().compute(results)
        assert cts.critical_failure is True
        assert cts.cts_reported <= 30.0
        # security's own weighted contribution reflects its true (low) score, not the CTS cap.
        assert cts.evaluator_contributions["security"] == pytest.approx(
            2.0 * DEFAULT_WEIGHTS["security"]
        )
        # every other module's contribution reflects its own true (high) score, unclamped.
        for name in EVALUATOR_NAMES:
            if name == "security":
                continue
            assert cts.evaluator_contributions[name] == pytest.approx(90.0 * DEFAULT_WEIGHTS[name])

    def test_cts_raw_preserves_ordering_the_clamp_destroys(self) -> None:
        """cts_reported collapses a security=29 run and a security=2 run to the same capped
        number; cts_raw must keep them distinguishable and correctly ordered."""
        scores_29 = {name: 90.0 for name in EVALUATOR_NAMES}
        scores_29["security"] = 29.0
        scores_2 = {name: 90.0 for name in EVALUATOR_NAMES}
        scores_2["security"] = 2.0

        cts_29 = CTSCalculator().compute(_results(scores_29))
        cts_2 = CTSCalculator().compute(_results(scores_2))

        # Both are critical failures, clamped to the same reported ceiling.
        assert cts_29.cts_reported <= 30.0
        assert cts_2.cts_reported <= 30.0
        assert cts_29.cts_reported == pytest.approx(cts_2.cts_reported)

        # But the raw score correctly orders the run with the less severe security failure higher.
        assert cts_29.cts_raw > cts_2.cts_raw

    def test_clamp_never_raises_a_score(self) -> None:
        """cts_reported must never exceed cts_raw -- the cap only ever lowers the score."""
        for security_score in (0.0, 2.0, 29.0, 29.9, 30.0, 50.0, 100.0):
            scores = {name: 80.0 for name in EVALUATOR_NAMES}
            scores["security"] = security_score
            cts = CTSCalculator().compute(_results(scores))
            assert cts.cts_reported <= cts.cts_raw + 1e-9

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
