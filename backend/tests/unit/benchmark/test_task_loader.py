"""``TaskLoader`` (PROJECT_SPEC_2 SS56)."""

from __future__ import annotations

import pytest

from app.benchmark.task_loader import TaskLoader
from app.core.exceptions import ValidationError
from app.environments.banking.seed_task import SEED_TASK


class TestTaskLoader:
    def test_loads_a_valid_seed_task(self) -> None:
        task = TaskLoader().load_from_dict(SEED_TASK)
        assert task.task_id == "banking-001"
        assert task.environment == "banking"

    def test_invalid_task_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            TaskLoader().load_from_dict({"title": "missing required fields"})

    def test_load_many_preserves_order(self) -> None:
        tasks = TaskLoader().load_many([SEED_TASK, SEED_TASK])
        assert len(tasks) == 2
