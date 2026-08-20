"""Add execution_mode to runs.

Revision ID: 0004_run_execution_mode
Revises: 0003_criteria_assessment
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_run_execution_mode"
down_revision: str | None = "0003_criteria_assessment"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add ``execution_mode``: distinguishes a run AgentAudit executed itself ("benchmark") from
    one it only observed via ``AgentAuditTracer`` for an independently running agent
    ("external"). Defaults every pre-existing row to "benchmark", which is accurate for all of
    them -- external-agent tracing did not exist before this column.
    """
    op.add_column(
        "runs",
        sa.Column("execution_mode", sa.String(length=20), nullable=False, server_default="benchmark"),
    )
    op.create_index("ix_runs_execution_mode", "runs", ["execution_mode"])


def downgrade() -> None:
    """Drop ``execution_mode``."""
    op.drop_index("ix_runs_execution_mode", table_name="runs")
    op.drop_column("runs", "execution_mode")
