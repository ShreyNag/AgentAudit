"""Rubric definitions and loader (PROJECT_SPEC_3 SS105-106)."""

from __future__ import annotations

import pytest

from app.core.constants import EVALUATOR_NAMES
from app.core.exceptions import ConfigurationError
from app.evaluation.rubric.definitions import RUBRICS
from app.evaluation.rubric.loader import RubricLoader


class TestRubricDefinitions:
    def test_every_evaluator_name_has_a_rubric(self) -> None:
        for name in EVALUATOR_NAMES:
            assert name in RUBRICS

    def test_every_rubric_has_five_levels(self) -> None:
        for rubric in RUBRICS.values():
            assert len(rubric.levels) == 5

    def test_level_for_score_returns_the_matching_band(self) -> None:
        rubric = RUBRICS["security"]
        assert rubric.level_for_score(95.0).name == "Excellent"
        assert rubric.level_for_score(10.0).name == "Critical Failure"
        assert rubric.level_for_score(60.0).name == "Acceptable"


class TestRubricLoader:
    def test_get_returns_the_correct_rubric(self) -> None:
        loader = RubricLoader()
        rubric = loader.get("planner")
        assert rubric.identifier == "planner"

    def test_get_unknown_evaluator_raises_configuration_error(self) -> None:
        loader = RubricLoader()
        with pytest.raises(ConfigurationError):
            loader.get("not-a-real-evaluator")

    def test_list_evaluator_names_matches_the_canonical_ten(self) -> None:
        loader = RubricLoader()
        assert set(loader.list_evaluator_names()) == set(EVALUATOR_NAMES)
