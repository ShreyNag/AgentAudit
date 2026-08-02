"""``tool_calls`` table (PROJECT_SPEC_1 SS83): one record per tool invocation."""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ToolCallModel(Base, TimestampMixin):
    """One tool invocation within a run's execution."""

    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="RESTRICT"), index=True)
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    validated_arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    execution_order: Mapped[int] = mapped_column(index=True)
    latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
