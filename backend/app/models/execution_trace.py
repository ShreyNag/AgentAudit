"""``execution_traces`` table (PROJECT_SPEC_1 SS81): the complete, immutable execution trace."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ExecutionTraceModel(Base, TimestampMixin):
    """The full serialized execution trace for one run, stored as structured JSON."""

    __tablename__ = "execution_traces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="RESTRICT"), unique=True, index=True
    )
    trace_json: Mapped[dict] = mapped_column(JSON)
    planner: Mapped[dict] = mapped_column(JSON, default=dict)
    reasoning: Mapped[dict] = mapped_column(JSON, default=dict)
    messages: Mapped[list] = mapped_column(JSON, default=list)
    trace_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
