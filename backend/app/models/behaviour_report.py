"""``behaviour_reports`` table (PROJECT_SPEC_1 SS87)."""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class BehaviourReportModel(Base, TimestampMixin):
    """Behavioural classification for one run.

    ``classification`` must be one of ``SAFE_CORRECT``, ``SAFE_BY_INCOMPETENCE``,
    ``UNSAFE_COMPLIANCE``, ``PARTIAL_SUCCESS`` (PROJECT_SPEC_1 SS87), enforced at the service
    layer against :data:`app.core.constants.BEHAVIOUR_CLASSIFICATIONS`.
    """

    __tablename__ = "behaviour_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="RESTRICT"), unique=True, index=True
    )
    classification: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
