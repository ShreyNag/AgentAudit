"""``failure_reports`` table (PROJECT_SPEC_1 SS88)."""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class FailureReportModel(Base, TimestampMixin):
    """Failure attribution for one run."""

    __tablename__ = "failure_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="RESTRICT"), unique=True, index=True
    )
    primary_failure: Mapped[str] = mapped_column(String(100), index=True)
    secondary_failures: Mapped[list] = mapped_column(JSON, default=list)
    affected_components: Mapped[list] = mapped_column(JSON, default=list)
    diagnostic_reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
