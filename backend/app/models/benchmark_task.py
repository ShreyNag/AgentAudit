"""``benchmark_tasks`` table (PROJECT_SPEC_1 SS77).

Ground truth is stored only here and must never be exposed to the Agent Under Test
(PROJECT_SPEC_1 SS62).
"""

from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class BenchmarkTaskModel(Base, TimestampMixin):
    """A single benchmark task, immutable after publication (PROJECT_SPEC_1 SS55)."""

    __tablename__ = "benchmark_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(50), index=True)
    difficulty: Mapped[str] = mapped_column(String(50))
    attack_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instruction: Mapped[str] = mapped_column(Text)
    ground_truth: Mapped[dict] = mapped_column(JSON)
    expected_tool_sequence: Mapped[list] = mapped_column(JSON, default=list)
    task_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
