"""``BenchmarkService`` (PROJECT_SPEC_2 SS17): environment/task discovery and seeding."""

from __future__ import annotations

# Importing app.environments registers every environment (and its BenchmarkEnvironmentMeta) on
# benchmark_registry; these seed_task modules provide the deterministic starter task(s) per
# environment used to populate the database on first run.
import app.environments  # noqa: E402,F401
from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.banking.seed_task import SEED_TASK as BANKING_SEED_TASK
from app.environments.email_env.seed_task import SEED_TASK as EMAIL_SEED_TASK
from app.environments.identity_documents.seed_task import (
    SEED_TASK_CALIBRATION as IDENTITY_DOCUMENTS_SEED_TASK_CALIBRATION,
)
from app.environments.identity_documents.seed_task import (
    SEED_TASK_REFUSAL as IDENTITY_DOCUMENTS_SEED_TASK_REFUSAL,
)
from app.environments.jailbreak.seed_task import SEED_TASK as JAILBREAK_SEED_TASK
from app.environments.marketplace.seed_task import SEED_TASK as MARKETPLACE_SEED_TASK
from app.environments.memory_poisoning.seed_task import SEED_TASK as MEMORY_POISONING_SEED_TASK
from app.environments.payments.seed_task import SEED_TASK as PAYMENTS_SEED_TASK
from app.environments.trip_planner.seed_task import SEED_TASK as TRIP_PLANNER_SEED_TASK
from app.models.benchmark_task import BenchmarkTaskModel
from app.repositories.benchmark_repository import (
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
)
from app.services.base import BaseService

_ALL_SEED_TASKS: list[dict[str, object]] = [
    BANKING_SEED_TASK,
    PAYMENTS_SEED_TASK,
    MARKETPLACE_SEED_TASK,
    TRIP_PLANNER_SEED_TASK,
    EMAIL_SEED_TASK,
    IDENTITY_DOCUMENTS_SEED_TASK_REFUSAL,
    IDENTITY_DOCUMENTS_SEED_TASK_CALIBRATION,
    JAILBREAK_SEED_TASK,
    MEMORY_POISONING_SEED_TASK,
]


class BenchmarkService(BaseService):
    """Environment/task discovery, and idempotent seeding of the benchmark database tables."""

    def __init__(
        self,
        benchmark_task_repository: BenchmarkTaskRepository,
        benchmark_environment_repository: BenchmarkEnvironmentRepository,
    ) -> None:
        """Bind the service to the repositories backing the benchmark database tables."""
        self._task_repository = benchmark_task_repository
        self._environment_repository = benchmark_environment_repository

    def list_registered_environments(self) -> list[BenchmarkEnvironmentMeta]:
        """Return every environment currently registered in-process (PROJECT_SPEC_2 SS54)."""
        return benchmark_registry.list_all()

    async def ensure_seeded(self) -> None:
        """Idempotently persist every registered environment and its seed task.

        Safe to call on every startup: existing rows are left untouched (PROJECT_SPEC_1 SS55 --
        tasks are immutable after publication).
        """
        for meta in benchmark_registry.list_all():
            if await self._environment_repository.get_by_name(meta.name) is None:
                await self._environment_repository.create(
                    name=meta.name,
                    description=meta.description,
                    version=meta.version,
                    toolset=meta.toolset,
                    difficulty_levels=meta.difficulty_levels,
                    environment_metadata=meta.metadata,
                )

        for seed_task in _ALL_SEED_TASKS:
            if await self._task_repository.get_by_task_id(str(seed_task["task_id"])) is None:
                await self._task_repository.create(
                    task_id=seed_task["task_id"],
                    title=seed_task["title"],
                    description=seed_task["description"],
                    environment=seed_task["environment"],
                    difficulty=seed_task["difficulty"],
                    attack_type=seed_task.get("attack_type"),
                    instruction=seed_task["instruction"],
                    ground_truth=seed_task["ground_truth"],
                    expected_tool_sequence=seed_task["expected_tool_sequence"],
                    task_metadata=seed_task.get("metadata", {}),
                )

    async def list_tasks(
        self, *, environment: str | None = None, page: int = 1, page_size: int = 50
    ) -> list[BenchmarkTaskModel]:
        """List persisted benchmark tasks, optionally filtered by environment."""
        return list(
            await self._task_repository.list(
                page=page, page_size=page_size, environment=environment
            )
        )

    async def get_task(self, task_id: str) -> BenchmarkTaskModel | None:
        """Return the persisted task registered under ``task_id``, or ``None``."""
        return await self._task_repository.get_by_task_id(task_id)
