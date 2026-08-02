"""Shared SQLAlchemy declarative base and reusable column mixins."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for every AgentAudit ORM model (PROJECT_SPEC_4 SS24)."""


class TimestampMixin:
    """Adds a server-side ``created_at`` timestamp, required on every table (PROJECT_SPEC_4
    SS91).
    """

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
