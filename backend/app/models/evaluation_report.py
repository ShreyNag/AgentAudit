"""``evaluation_reports`` table (PROJECT_SPEC_1 SS85): report-level evaluation output only.

Individual evaluator scores live in :class:`~app.models.evaluation_score.EvaluationScoreModel`.
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class EvaluationReportModel(Base, TimestampMixin):
    """The composite evaluation report for one run, including the Composite Trust Score."""

    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="RESTRICT"), unique=True, index=True
    )
    overall_reasoning: Mapped[str] = mapped_column(Text)
    overall_summary: Mapped[str] = mapped_column(Text)
    cts: Mapped[float] = mapped_column(Float, index=True)
    planner_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    integrity_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
