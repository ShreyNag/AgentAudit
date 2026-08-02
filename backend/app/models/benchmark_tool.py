"""``benchmark_tools`` table.

PROJECT_SPEC_1 SS76 lists ``benchmark_tools`` among the primary tables but does not give it a
dedicated field section (unlike the other 13). Fields below are inferred from the tool
metadata contract in PROJECT_SPEC_1 SS65 ("Every tool exposes: Name, Description, Version,
Environment, Input Schema, Output Schema, Capabilities, Supported Operations") since that is
the only place the specification enumerates what a tool's persisted record should contain.
"""

from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class BenchmarkToolModel(Base, TimestampMixin):
    """Registered metadata for one tool implementation, scoped to an environment."""

    __tablename__ = "benchmark_tools"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(1000))
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    environment: Mapped[str] = mapped_column(String(50), index=True)
    input_schema: Mapped[dict] = mapped_column(JSON)
    output_schema: Mapped[dict] = mapped_column(JSON)
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    supported_operations: Mapped[list] = mapped_column(JSON, default=list)
