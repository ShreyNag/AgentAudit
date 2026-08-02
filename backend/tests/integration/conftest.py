"""Shared fixtures for repository/database integration tests.

Schema is created directly via ``Base.metadata.create_all`` against an in-memory SQLite
database rather than by running Alembic migrations, which is the standard, lighter-weight way
to exercise the repository layer in isolation (PROJECT_SPEC_2 SS123 designates real MySQL for
full integration testing in CI; see ``.github/workflows/ci.yml``).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure every model is registered on Base.metadata before create_all runs.
import app.models  # noqa: F401
from app.database.base import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` bound to a fresh, isolated in-memory SQLite schema."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
