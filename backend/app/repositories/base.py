"""Generic base repository.

Implements the common CRUD/query shape described in PROJECT_SPEC_2 SS18-SS19 and
PROJECT_SPEC_6 SS19: ``create/update/delete/find/list/exists``. Concrete repositories subclass
this with a specific ORM model and add resource-specific query methods only -- no business
rules belong here or in any subclass (PROJECT_SPEC_2 SS84).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async CRUD repository for a single SQLAlchemy model.

    Args:
        session: The request-scoped :class:`~sqlalchemy.ext.asyncio.AsyncSession` to operate
            on. The repository never opens, commits, or closes its own session -- that is the
            responsibility of :func:`app.database.session.get_db` / the calling service.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        """Bind this repository instance to a request-scoped session."""
        self.session = session

    async def create(self, **fields: Any) -> ModelT:
        """Insert a new row and return the persisted, refreshed instance."""
        instance = self.model(**fields)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get(self, record_id: int) -> ModelT | None:
        """Return the row with primary key ``record_id``, or ``None`` if it does not exist."""
        return await self.session.get(self.model, record_id)

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        order_by: str | None = None,
        descending: bool = True,
        **filters: Any,
    ) -> Sequence[ModelT]:
        """Return a page of rows matching ``filters`` (PROJECT_SPEC_2 SS103).

        Args:
            page: 1-indexed page number.
            page_size: Rows per page, clamped to ``MAX_PAGE_SIZE``.
            order_by: Column name to sort by; defaults to the model's primary key.
            descending: Sort direction.
            **filters: Exact-match column filters, e.g. ``status="completed"``.
        """
        page_size = min(page_size, MAX_PAGE_SIZE)
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, filters)

        sort_column = getattr(self.model, order_by) if order_by else self._primary_key_column()
        stmt = stmt.order_by(sort_column.desc() if descending else sort_column.asc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        """Return the number of rows matching ``filters``."""
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def count_grouped_by(self, column_name: str) -> list[dict[str, Any]]:
        """Return ``[{column_name: value, "count": n}, ...]`` for every distinct value.

        Used by dashboard analytics (e.g. runs grouped by provider or environment) without
        needing a bespoke aggregate method per model (PROJECT_SPEC_2 SS89).
        """
        column = getattr(self.model, column_name)
        stmt = select(column, func.count()).group_by(column)
        result = await self.session.execute(stmt)
        return [{column_name: value, "count": count} for value, count in result.all()]

    async def find_one(self, **filters: Any) -> ModelT | None:
        """Return the first row matching ``filters``, or ``None``."""
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt.limit(1))
        return result.scalars().first()

    async def exists(self, **filters: Any) -> bool:
        """Return whether at least one row matches ``filters``."""
        return await self.count(**filters) > 0

    async def update(self, record_id: int, **fields: Any) -> ModelT | None:
        """Update the row with primary key ``record_id`` and return the refreshed instance."""
        instance = await self.get(record_id)
        if instance is None:
            return None
        for key, value in fields.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, record_id: int) -> bool:
        """Delete the row with primary key ``record_id``. Returns whether a row was deleted.

        Note: PROJECT_SPEC_1 SS91 forbids cascade deletes of execution history; this generic
        delete is intended for non-historical resources (e.g. draft benchmark definitions,
        provider registrations) rather than runs/traces/evaluations.
        """
        instance = await self.get(record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    def _primary_key_column(self) -> Any:
        """Return the model's single primary-key column, for default ordering."""
        return list(self.model.__mapper__.primary_key)[0]

    def _apply_filters(self, stmt: Any, filters: dict[str, Any]) -> Any:
        """Apply exact-match ``WHERE`` clauses for each non-``None`` filter value."""
        for key, value in filters.items():
            if value is None:
                continue
            stmt = stmt.where(getattr(self.model, key) == value)
        return stmt
