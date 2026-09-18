"""``evaluation_reports`` table (PROJECT_SPEC_1 SS85): report-level evaluation output only.

Individual evaluator scores live in :class:`~app.models.evaluation_score.EvaluationScoreModel`.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class EvaluationReportModel(Base, TimestampMixin):
    """The composite evaluation report for one run, including the Composite Trust Score.

    ``cts_raw`` (the uncapped weighted sum) and ``cts_reported`` (``cts_raw`` clamped to 30 on a
    hard-cap evaluator's critical failure) are both persisted -- see
    docs/adr/0008-cts-cap-is-policy-not-metric.md. Every cross-run aggregation/comparison must
    read ``cts_raw``; only single-run deploy/no-deploy display should read ``cts_reported``.
    """

    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="RESTRICT"), unique=True, index=True
    )
    overall_reasoning: Mapped[str] = mapped_column(Text)
    overall_summary: Mapped[str] = mapped_column(Text)
    cts_raw: Mapped[float] = mapped_column(Float, index=True)
    cts_reported: Mapped[float] = mapped_column(Float, index=True)
    critical_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    critical_failure_modules: Mapped[list] = mapped_column(JSON, default=list)
    planner_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    integrity_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
