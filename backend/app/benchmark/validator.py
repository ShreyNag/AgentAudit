"""``BenchmarkValidator`` (PROJECT_SPEC_2 SS68/SS113): pre-execution validation.

Execution must not begin if validation fails (PROJECT_SPEC_2 SS113).
"""

from __future__ import annotations

from app.benchmark.models import Task
from app.benchmark.registry import BenchmarkRegistry
from app.core.exceptions import ValidationError
from app.tools.registry import ToolRegistry


class BenchmarkValidator:
    """Validates that a task can actually be executed before the runner starts."""

    def __init__(self, benchmark_registry: BenchmarkRegistry, tool_registry: ToolRegistry) -> None:
        """Bind the validator to the registries it checks task requirements against."""
        self._benchmark_registry = benchmark_registry
        self._tool_registry = tool_registry

    def validate(self, task: Task) -> None:
        """Validate ``task`` is executable.

        Raises:
            ValidationError: if the task's environment is not registered, if any tool in its
                expected tool sequence is not registered, or if ground truth is missing.
        """
        if not self._benchmark_registry.is_registered(task.environment):
            raise ValidationError(
                f"Task '{task.task_id}' references unregistered environment "
                f"'{task.environment}'."
            )
        if not task.ground_truth:
            raise ValidationError(f"Task '{task.task_id}' has no ground truth defined.")

        missing_tools = [
            tool_name
            for tool_name in task.expected_tool_sequence
            if not self._tool_registry.is_registered(tool_name)
        ]
        if missing_tools:
            raise ValidationError(
                f"Task '{task.task_id}' expects unregistered tools: {', '.join(missing_tools)}."
            )
