"""Request schema for externally-produced execution traces (PROJECT_SPEC_2 SS96's route
conventions, extended to runs AgentAudit observed rather than executed itself).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.trace.models import ExecutionTrace


class ExternalRunIngestRequest(BaseModel):
    """One externally-produced run's complete trace, ready to persist and evaluate.

    ``trace`` is a full ``app.trace.models.ExecutionTrace`` -- typically produced by calling
    ``AgentAuditTracer.finish()`` in-process and serializing its return value (e.g.
    ``trace.model_dump(mode="json")``).
    """

    trace: ExecutionTrace
    environment: str = "external"
    provider: str = "external"
    model: str = "external"
    task_id: str | None = None
    status: str = "completed"
    task_instruction: str = Field(
        default="",
        description=(
            "Used only when task_id is absent or does not match an already-registered "
            "benchmark task, to seed the placeholder task's instruction text shown to the "
            "Judge. Ignored when reusing a registered task."
        ),
    )
    ground_truth: dict[str, object] = Field(
        default_factory=dict,
        description="Same placeholder-only caveat as task_instruction.",
    )
