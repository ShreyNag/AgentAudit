"""Benchmark-side repositories: tasks, environments, and tools (PROJECT_SPEC_1 SS77-79)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.benchmark_environment import BenchmarkEnvironmentModel
from app.models.benchmark_task import BenchmarkTaskModel
from app.models.benchmark_tool import BenchmarkToolModel
from app.repositories.base import BaseRepository


class BenchmarkTaskRepository(BaseRepository[BenchmarkTaskModel]):
    """Persistence for :class:`~app.models.benchmark_task.BenchmarkTaskModel`."""

    model = BenchmarkTaskModel

    async def get_by_task_id(self, task_id: str) -> BenchmarkTaskModel | None:
        """Return the task with the given external ``task_id``, or ``None``."""
        return await self.find_one(task_id=task_id)

    async def list_by_environment(self, environment: str) -> Sequence[BenchmarkTaskModel]:
        """Return every task belonging to a given benchmark environment."""
        stmt = select(BenchmarkTaskModel).where(BenchmarkTaskModel.environment == environment)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class BenchmarkEnvironmentRepository(BaseRepository[BenchmarkEnvironmentModel]):
    """Persistence for :class:`~app.models.benchmark_environment.BenchmarkEnvironmentModel`."""

    model = BenchmarkEnvironmentModel

    async def get_by_name(self, name: str) -> BenchmarkEnvironmentModel | None:
        """Return the environment registration with the given ``name``, or ``None``."""
        return await self.find_one(name=name)


class BenchmarkToolRepository(BaseRepository[BenchmarkToolModel]):
    """Persistence for :class:`~app.models.benchmark_tool.BenchmarkToolModel`."""

    model = BenchmarkToolModel

    async def get_by_name(self, name: str) -> BenchmarkToolModel | None:
        """Return the tool registration with the given ``name``, or ``None``."""
        return await self.find_one(name=name)

    async def list_by_environment(self, environment: str) -> Sequence[BenchmarkToolModel]:
        """Return every tool registered for a given benchmark environment."""
        stmt = select(BenchmarkToolModel).where(BenchmarkToolModel.environment == environment)
        result = await self.session.execute(stmt)
        return result.scalars().all()
