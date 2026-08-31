"""``runs`` table (PROJECT_SPEC_1 SS80): one row per benchmark execution."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class RunModel(Base, TimestampMixin):
    """Represents one benchmark execution; every evaluation corresponds to exactly one run."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    benchmark_task_id: Mapped[int] = mapped_column(
        ForeignKey("benchmark_tasks.id", ondelete="RESTRICT"), index=True
    )
    provider: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str] = mapped_column(String(100), index=True)
    judge_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    judge_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="queued")
    # "benchmark" (AgentAudit drove the execution) or "external" (an independently running agent
    # was only observed -- see app.trace.tracer.AgentAuditTracer). Distinguishes the two without
    # a second runs-like table (app.core.constants.EXECUTION_MODES).
    execution_mode: Mapped[str] = mapped_column(String(20), index=True, default="benchmark")
    execution_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_time: Mapped[dt.datetime | None] = mapped_column(nullable=True)
    end_time: Mapped[dt.datetime | None] = mapped_column(nullable=True)
