"""Add criteria_assessment to evaluation_scores.

Revision ID: 0003_criteria_assessment
Revises: 0002_eval_score_expected_actual
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_criteria_assessment"
down_revision: str | None = "0002_eval_score_expected_actual"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add the ``criteria_assessment`` column: one followed/partially_followed/ignored verdict
    per rubric criterion, alongside the aggregate score the Judge already reports.

    Added nullable, backfilled to an empty JSON array for pre-existing rows, then tightened to
    ``NOT NULL`` -- mirrors 0002's expected_outcome/actual_outcome pattern.
    """
    op.add_column("evaluation_scores", sa.Column("criteria_assessment", sa.JSON(), nullable=True))

    evaluation_scores = sa.table("evaluation_scores", sa.column("criteria_assessment", sa.JSON()))
    op.execute(evaluation_scores.update().values(criteria_assessment=[]))

    op.alter_column(
        "evaluation_scores", "criteria_assessment", existing_type=sa.JSON(), nullable=False
    )


def downgrade() -> None:
    """Drop the ``criteria_assessment`` column."""
    op.drop_column("evaluation_scores", "criteria_assessment")
