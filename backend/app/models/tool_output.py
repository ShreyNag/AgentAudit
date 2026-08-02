"""``tool_outputs`` table (PROJECT_SPEC_1 SS84).

Ground-truth comparisons for a tool output are performed later, by evaluators -- this table
only stores the observed output and (optionally) the ground truth snapshot it will eventually
be compared against.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ToolOutputModel(Base, TimestampMixin):
    """The result of one tool invocation."""

    __tablename__ = "tool_outputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tool_call_id: Mapped[int] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="RESTRICT"), unique=True, index=True
    )
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    ground_truth: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    output_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
