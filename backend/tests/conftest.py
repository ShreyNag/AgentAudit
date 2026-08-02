"""Shared pytest fixtures for the AgentAudit backend test suite."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the cached :func:`get_settings` singleton before every test.

    Prevents state or environment-variable overrides made by one test from leaking into the
    next, since ``lru_cache`` would otherwise pin the first-constructed ``Settings`` instance.
    """
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """An ``httpx.AsyncClient`` wired directly to the FastAPI app via ASGI transport.

    Creates the full schema against the in-memory SQLite database before yielding: the ASGI
    transport does not run FastAPI's lifespan handlers, so nothing else would ever create it.
    """
    import app.models  # noqa: F401 - registers every model on Base.metadata
    from app.database.base import Base
    from app.database.session import get_database
    from app.main import create_app

    get_database.cache_clear()
    app = create_app()

    database = get_database()
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    get_database.cache_clear()
