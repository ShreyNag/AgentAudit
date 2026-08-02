"""``system_settings`` table (PROJECT_SPEC_1 SS89).

Only application settings belong here; secrets remain in environment variables
(PROJECT_SPEC_1 SS89/SS101).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SystemSettingsModel(Base):
    """A single runtime configuration key/value pair.

    Uses ``updated_at`` rather than :class:`~app.database.base.TimestampMixin`'s
    ``created_at`` since settings are mutable by design (PROJECT_SPEC_1 SS89's field list is
    ``id, key, value, description, updated_at``).
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
