"""``TaskLoader`` (PROJECT_SPEC_2 SS56): loads and validates task definitions.

The loader never executes a task -- it only parses, validates, and returns :class:`Task`
domain objects for the runner to consume later.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.benchmark.models import Task
from app.core.exceptions import ValidationError as AgentAuditValidationError


class TaskLoader:
    """Parses raw task definitions into validated :class:`~app.benchmark.models.Task` objects."""

    def load_from_dict(self, data: dict[str, object]) -> Task:
        """Validate and construct a single :class:`Task` from a raw mapping.

        Raises:
            ValidationError: if ``data`` does not conform to the task schema.
        """
        try:
            return Task.model_validate(data)
        except ValidationError as exc:
            raise AgentAuditValidationError(f"Invalid benchmark task definition: {exc}") from exc

    def load_many(self, items: list[dict[str, object]]) -> list[Task]:
        """Validate and construct many tasks, preserving input order."""
        return [self.load_from_dict(item) for item in items]
