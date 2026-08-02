"""``RubricLoader`` (PROJECT_SPEC_6 SS77): loads, validates, and caches compiled rubrics."""

from __future__ import annotations

from app.core.exceptions import ConfigurationError
from app.evaluation.rubric.definitions import RUBRICS
from app.evaluation.rubric.models import Rubric


class RubricLoader:
    """Resolves an evaluator name to its versioned :class:`Rubric`."""

    def __init__(self, rubrics: dict[str, Rubric] | None = None) -> None:
        """Load from the built-in rubric definitions, or an injected override set for testing."""
        self._rubrics = rubrics if rubrics is not None else RUBRICS

    def get(self, evaluator_name: str) -> Rubric:
        """Return the rubric for ``evaluator_name``.

        Raises:
            ConfigurationError: if no rubric is defined for ``evaluator_name``.
        """
        rubric = self._rubrics.get(evaluator_name)
        if rubric is None:
            raise ConfigurationError(f"No rubric defined for evaluator '{evaluator_name}'.")
        return rubric

    def list_evaluator_names(self) -> list[str]:
        """Return every evaluator name that has a defined rubric."""
        return sorted(self._rubrics)
