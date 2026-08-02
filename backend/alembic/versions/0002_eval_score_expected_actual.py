"""Add expected_outcome/actual_outcome to evaluation_scores.

Revision ID: 0002_eval_score_expected_actual
Revises: 0001_initial_schema
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_eval_score_expected_actual"
down_revision: str | None = "0001_initial_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add the ``expected_outcome``/``actual_outcome`` columns the Judge now always reports.

    MySQL rejects a literal ``DEFAULT`` on ``TEXT`` columns, so these are added nullable,
    backfilled for any pre-existing rows, then tightened to ``NOT NULL``.
    """
    op.add_column("evaluation_scores", sa.Column("expected_outcome", sa.Text(), nullable=True))
    op.add_column("evaluation_scores", sa.Column("actual_outcome", sa.Text(), nullable=True))

    evaluation_scores = sa.table(
        "evaluation_scores",
        sa.column("expected_outcome", sa.Text()),
        sa.column("actual_outcome", sa.Text()),
    )
    op.execute(evaluation_scores.update().values(expected_outcome="", actual_outcome=""))

    op.alter_column(
        "evaluation_scores", "expected_outcome", existing_type=sa.Text(), nullable=False
    )
    op.alter_column("evaluation_scores", "actual_outcome", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    """Drop the ``expected_outcome``/``actual_outcome`` columns."""
    op.drop_column("evaluation_scores", "actual_outcome")
    op.drop_column("evaluation_scores", "expected_outcome")
