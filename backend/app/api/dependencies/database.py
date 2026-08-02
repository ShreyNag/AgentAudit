"""Database-session dependency wiring for the API layer (PROJECT_SPEC_2 SS9)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
"""Type alias for injecting a request-scoped :class:`AsyncSession` into a route handler."""
