"""``benchmark_environments`` table (PROJECT_SPEC_1 SS78)."""

from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class BenchmarkEnvironmentModel(Base, TimestampMixin):
    """Metadata describing one benchmark environment (travel, email, banking, ...)."""

    __tablename__ = "benchmark_environments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(1000))
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    toolset: Mapped[list] = mapped_column(JSON, default=list)
    difficulty_levels: Mapped[list] = mapped_column(JSON, default=list)
    environment_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
