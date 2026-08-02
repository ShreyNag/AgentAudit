"""``trace_events`` table (PROJECT_SPEC_1 SS82): powers the execution timeline."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class TraceEventModel(Base, TimestampMixin):
    """A single, immutable, ordered event within an execution trace."""

    __tablename__ = "trace_events"
    __table_args__ = (
        UniqueConstraint("run_id", "event_number", name="uq_trace_events_run_event_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="RESTRICT"), index=True)
    event_number: Mapped[int] = mapped_column(index=True)
    timestamp: Mapped[dt.datetime] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    component: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ok")
