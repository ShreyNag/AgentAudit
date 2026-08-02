"""Async engine and per-request session management.

Each API request receives its own :class:`~sqlalchemy.ext.asyncio.AsyncSession`, committed on
success and rolled back on error, per PROJECT_SPEC_2 SS19. Execution and evaluation each use
their own transaction (PROJECT_SPEC_1 SS96) by requesting a fresh session rather than sharing
one across service calls.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.core.exceptions import ConfigurationError


class Database:
    """Owns the process-wide async engine and session factory for one configuration."""

    def __init__(self, settings: Settings) -> None:
        """Create the async engine and session factory from ``settings.database_url``."""
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
        if settings.is_sqlite:
            # A plain (non-StaticPool) SQLite engine hands out a fresh connection per
            # checkout; for an in-memory DSN that means a *blank* database on every
            # request, silently losing all data between sessions. StaticPool pins a single
            # shared connection so schema/data persist for the lifetime of the engine -- the
            # correct behavior for SQLite's development/test-only role (PROJECT_SPEC_1 SS74).
            engine_kwargs = {"poolclass": StaticPool}
            connect_args = {"check_same_thread": False}
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            echo=False,
            connect_args=connect_args,
            **engine_kwargs,
        )
        if settings.is_sqlite:
            # SQLite enforces foreign keys (RESTRICT/CASCADE) only when explicitly turned on per
            # connection -- without this, SQLite (dev/test only) silently allows deletes that
            # would correctly fail against MySQL 8+ (PROJECT_SPEC_1 SS74/SS91), masking bugs.
            @event.listens_for(self._engine.sync_engine, "connect")
            def _enable_sqlite_foreign_keys(dbapi_connection: object, _record: object) -> None:
                cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Return the underlying async engine."""
        return self._engine

    def session(self) -> AsyncSession:
        """Create a new, unopened :class:`AsyncSession` bound to this engine."""
        return self._session_factory()

    async def check_connectivity(self) -> bool:
        """Run a trivial query to verify the database is reachable.

        Used by startup validation (PROJECT_SPEC_2 SS23) and the ``/health/database`` endpoint.
        Raises :class:`ConfigurationError` if the database cannot be reached.
        """
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 - normalized into a typed error
            raise ConfigurationError(f"Database is not reachable: {exc}") from exc
        return True

    async def dispose(self) -> None:
        """Dispose of the engine's connection pool during application shutdown."""
        await self._engine.dispose()


@lru_cache
def get_database() -> Database:
    """Return the process-wide cached :class:`Database` instance."""
    return Database(get_settings())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped :class:`AsyncSession`.

    Commits on success, rolls back on any exception, and always closes the session
    (PROJECT_SPEC_2 SS19).
    """
    database = get_database()
    session = database.session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
