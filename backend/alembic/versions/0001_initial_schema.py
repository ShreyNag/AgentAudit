"""Initial schema: all 14 tables from PROJECT_SPEC_1 SS76-SS89.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create all 14 AgentAudit tables and their indexes/foreign keys."""
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("provider_name"),
    )
    op.create_index("ix_providers_provider_name", "providers", ["provider_name"])
    op.create_index("ix_providers_provider_type", "providers", ["provider_type"])

    op.create_table(
        "benchmark_environments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("toolset", sa.JSON(), nullable=False),
        sa.Column("difficulty_levels", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_benchmark_environments_name", "benchmark_environments", ["name"])

    op.create_table(
        "benchmark_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=False),
        sa.Column("attack_type", sa.String(length=100), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("ground_truth", sa.JSON(), nullable=False),
        sa.Column("expected_tool_sequence", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_benchmark_tasks_task_id", "benchmark_tasks", ["task_id"])
    op.create_index("ix_benchmark_tasks_environment", "benchmark_tasks", ["environment"])

    op.create_table(
        "benchmark_tools",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("supported_operations", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_benchmark_tools_name", "benchmark_tools", ["name"])
    op.create_index("ix_benchmark_tools_environment", "benchmark_tools", ["environment"])

    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_uuid", sa.String(length=36), nullable=False),
        sa.Column(
            "benchmark_task_id",
            sa.Integer(),
            sa.ForeignKey("benchmark_tasks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("judge_provider", sa.String(length=50), nullable=True),
        sa.Column("judge_model", sa.String(length=100), nullable=True),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("execution_time", sa.Float(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_uuid"),
    )
    op.create_index("ix_runs_run_uuid", "runs", ["run_uuid"])
    op.create_index("ix_runs_benchmark_task_id", "runs", ["benchmark_task_id"])
    op.create_index("ix_runs_provider", "runs", ["provider"])
    op.create_index("ix_runs_model", "runs", ["model"])
    op.create_index("ix_runs_environment", "runs", ["environment"])
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_index("ix_runs_created_at", "runs", ["created_at"])

    op.create_table(
        "execution_traces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("trace_json", sa.JSON(), nullable=False),
        sa.Column("planner", sa.JSON(), nullable=False),
        sa.Column("reasoning", sa.JSON(), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("statistics", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_execution_traces_run_id", "execution_traces", ["run_id"])

    op.create_table(
        "trace_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("event_number", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("component", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("latency", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ok"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id", "event_number", name="uq_trace_events_run_event_number"),
    )
    op.create_index("ix_trace_events_run_id", "trace_events", ["run_id"])
    op.create_index("ix_trace_events_event_number", "trace_events", ["event_number"])
    op.create_index("ix_trace_events_timestamp", "trace_events", ["timestamp"])
    op.create_index("ix_trace_events_event_type", "trace_events", ["event_type"])

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("validated_arguments", sa.JSON(), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.Column("latency", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("error", sa.String(length=2000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_tool_calls_run_id", "tool_calls", ["run_id"])
    op.create_index("ix_tool_calls_tool_name", "tool_calls", ["tool_name"])
    op.create_index("ix_tool_calls_execution_order", "tool_calls", ["execution_order"])

    op.create_table(
        "tool_outputs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tool_call_id",
            sa.Integer(),
            sa.ForeignKey("tool_calls.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("ground_truth", sa.JSON(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("tool_call_id"),
    )
    op.create_index("ix_tool_outputs_tool_call_id", "tool_outputs", ["tool_call_id"])

    op.create_table(
        "evaluation_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("overall_reasoning", sa.Text(), nullable=False),
        sa.Column("overall_summary", sa.Text(), nullable=False),
        sa.Column("cts", sa.Float(), nullable=False),
        sa.Column("planner_summary", sa.Text(), nullable=True),
        sa.Column("security_summary", sa.Text(), nullable=True),
        sa.Column("integrity_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_evaluation_reports_run_id", "evaluation_reports", ["run_id"])
    op.create_index("ix_evaluation_reports_cts", "evaluation_reports", ["cts"])

    op.create_table(
        "evaluation_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("evaluator_name", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("rubric_level", sa.String(length=50), nullable=False),
        sa.Column("matched_criteria", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id", "evaluator_name", name="uq_evaluation_scores_run_evaluator"),
    )
    op.create_index("ix_evaluation_scores_run_id", "evaluation_scores", ["run_id"])
    op.create_index("ix_evaluation_scores_evaluator_name", "evaluation_scores", ["evaluator_name"])

    op.create_table(
        "behaviour_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("classification", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_behaviour_reports_run_id", "behaviour_reports", ["run_id"])
    op.create_index("ix_behaviour_reports_classification", "behaviour_reports", ["classification"])

    op.create_table(
        "failure_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("primary_failure", sa.String(length=100), nullable=False),
        sa.Column("secondary_failures", sa.JSON(), nullable=False),
        sa.Column("affected_components", sa.JSON(), nullable=False),
        sa.Column("diagnostic_reasoning", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_failure_reports_run_id", "failure_reports", ["run_id"])
    op.create_index("ix_failure_reports_primary_failure", "failure_reports", ["primary_failure"])

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_system_settings_key", "system_settings", ["key"])


def downgrade() -> None:
    """Drop all 14 AgentAudit tables in reverse dependency order."""
    op.drop_table("system_settings")
    op.drop_table("failure_reports")
    op.drop_table("behaviour_reports")
    op.drop_table("evaluation_scores")
    op.drop_table("evaluation_reports")
    op.drop_table("tool_outputs")
    op.drop_table("tool_calls")
    op.drop_table("trace_events")
    op.drop_table("execution_traces")
    op.drop_table("runs")
    op.drop_table("benchmark_tools")
    op.drop_table("benchmark_tasks")
    op.drop_table("benchmark_environments")
    op.drop_table("providers")
