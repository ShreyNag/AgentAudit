"""``evaluation_scores`` table (PROJECT_SPEC_1 SS86): one row per evaluator, per run.

Adding a new evaluator requires inserting only additional rows here -- never a schema
migration (PROJECT_SPEC_1 SS86).
"""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class EvaluationScoreModel(Base, TimestampMixin):
    """The independent output of a single evaluator for a single run."""

    __tablename__ = "evaluation_scores"
    __table_args__ = (
        UniqueConstraint("run_id", "evaluator_name", name="uq_evaluation_scores_run_evaluator"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="RESTRICT"), index=True)
    evaluator_name: Mapped[str] = mapped_column(String(100), index=True)
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text)
    expected_outcome: Mapped[str] = mapped_column(Text, default="")
    actual_outcome: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    rubric_level: Mapped[str] = mapped_column(String(50))
    matched_criteria: Mapped[list] = mapped_column(JSON, default=list)
    criteria_assessment: Mapped[list] = mapped_column(JSON, default=list)
