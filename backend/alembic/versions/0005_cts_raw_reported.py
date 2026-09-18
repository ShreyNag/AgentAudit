"""Split evaluation_reports.cts into cts_raw/cts_reported, add critical_failure fields.

Revision ID: 0005_cts_raw_reported
Revises: 0004_run_execution_mode
Create Date: 2026-09-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_cts_raw_reported"
down_revision: str | None = "0004_run_execution_mode"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Split the single clamped ``cts`` column into ``cts_raw`` (uncapped weighted sum, used for
    every cross-run aggregation/comparison) and ``cts_reported`` (``cts_raw`` clamped to 30 on a
    hard-cap evaluator's critical failure, used for single-run deploy/no-deploy display) -- see
    docs/adr/0008-cts-cap-is-policy-not-metric.md. Also adds ``critical_failure`` and
    ``critical_failure_modules``.

    Pre-existing rows only ever persisted the clamped value, so the uncapped weighted sum can't be
    recovered for them: ``cts_raw`` is backfilled to the old ``cts`` value (the most honest
    available number) and ``critical_failure``/``critical_failure_modules`` backfill to
    False/``[]`` -- consistent with ``cts_raw == cts_reported``, i.e. "no retroactive capping is
    known to have applied."
    """
    op.drop_index("ix_evaluation_reports_cts", table_name="evaluation_reports")
    op.alter_column("evaluation_reports", "cts", new_column_name="cts_reported")
    op.create_index(
        "ix_evaluation_reports_cts_reported", "evaluation_reports", ["cts_reported"]
    )

    op.add_column("evaluation_reports", sa.Column("cts_raw", sa.Float(), nullable=True))
    evaluation_reports = sa.table(
        "evaluation_reports",
        sa.column("cts_raw", sa.Float()),
        sa.column("cts_reported", sa.Float()),
    )
    op.execute(evaluation_reports.update().values(cts_raw=evaluation_reports.c.cts_reported))
    op.alter_column("evaluation_reports", "cts_raw", existing_type=sa.Float(), nullable=False)
    op.create_index("ix_evaluation_reports_cts_raw", "evaluation_reports", ["cts_raw"])

    op.add_column(
        "evaluation_reports",
        sa.Column("critical_failure", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.add_column(
        "evaluation_reports", sa.Column("critical_failure_modules", sa.JSON(), nullable=True)
    )
    modules_table = sa.table(
        "evaluation_reports", sa.column("critical_failure_modules", sa.JSON())
    )
    op.execute(modules_table.update().values(critical_failure_modules=[]))
    op.alter_column(
        "evaluation_reports",
        "critical_failure_modules",
        existing_type=sa.JSON(),
        nullable=False,
    )


def downgrade() -> None:
    """Drop ``critical_failure``/``critical_failure_modules``/``cts_raw``, restore ``cts``."""
    op.drop_column("evaluation_reports", "critical_failure_modules")
    op.drop_column("evaluation_reports", "critical_failure")

    op.drop_index("ix_evaluation_reports_cts_raw", table_name="evaluation_reports")
    op.drop_column("evaluation_reports", "cts_raw")

    op.drop_index("ix_evaluation_reports_cts_reported", table_name="evaluation_reports")
    op.alter_column("evaluation_reports", "cts_reported", new_column_name="cts")
    op.create_index("ix_evaluation_reports_cts", "evaluation_reports", ["cts"])
