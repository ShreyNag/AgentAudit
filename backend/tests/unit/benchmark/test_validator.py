"""``BenchmarkValidator`` (PROJECT_SPEC_2 SS68/SS113): execution must not start if this fails."""

from __future__ import annotations

import pytest

import app.environments  # noqa: F401 - triggers environment + benchmark_registry registration
import app.tools.implementations  # noqa: F401 - triggers tool registration
from app.benchmark.registry import benchmark_registry
from app.benchmark.task_loader import TaskLoader
from app.benchmark.validator import BenchmarkValidator
from app.core.exceptions import ValidationError
from app.environments.banking.seed_task import SEED_TASK
from app.tools.registry import tool_registry


@pytest.fixture
def validator() -> BenchmarkValidator:
    return BenchmarkValidator(benchmark_registry, tool_registry)


class TestBenchmarkValidator:
    def test_valid_seed_task_passes(self, validator: BenchmarkValidator) -> None:
        task = TaskLoader().load_from_dict(SEED_TASK)
        validator.validate(task)  # must not raise

    def test_unregistered_environment_raises(self, validator: BenchmarkValidator) -> None:
        task = TaskLoader().load_from_dict({**SEED_TASK, "environment": "not-a-real-environment"})
        with pytest.raises(ValidationError):
            validator.validate(task)

    def test_missing_ground_truth_raises(self, validator: BenchmarkValidator) -> None:
        task = TaskLoader().load_from_dict({**SEED_TASK, "ground_truth": {}})
        with pytest.raises(ValidationError):
            validator.validate(task)

    def test_unregistered_expected_tool_raises(self, validator: BenchmarkValidator) -> None:
        task = TaskLoader().load_from_dict(
            {**SEED_TASK, "expected_tool_sequence": ["not_a_real_tool"]}
        )
        with pytest.raises(ValidationError):
            validator.validate(task)
