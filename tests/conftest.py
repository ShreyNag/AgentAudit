"""Fixtures for the top-level, cross-cutting end-to-end test suite (PROJECT_SPEC_2 SS124).

These tests intentionally live outside ``backend/`` (PROJECT_SPEC_1 SS19) rather than reusing
``backend/tests/conftest.py`` via pytest's string-based plugin loading, which would depend on
fragile assumptions about sys.path ordering given that both directories are named ``tests``.
Instead, ``backend/`` is added to ``sys.path`` and the same small set of fixtures is defined
directly here.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import get_settings  # noqa: E402 - must follow the sys.path fix-up above


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the cached Settings singleton and point at an isolated in-memory SQLite database."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """An ``httpx.AsyncClient`` wired to the FastAPI app, with the full schema pre-created."""
    import app.models  # noqa: F401 - registers every model on Base.metadata
    from app.database.base import Base
    from app.database.session import get_database
    from app.main import create_app

    get_database.cache_clear()
    app_instance = create_app()

    database = get_database()
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    get_database.cache_clear()
