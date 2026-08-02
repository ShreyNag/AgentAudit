"""Trace serialization (PROJECT_SPEC_1 SS67, PROJECT_SPEC_2 SS81): deterministic, versioned JSON."""

from __future__ import annotations

from typing import Any

from app.trace.models import ExecutionTrace


def serialize_trace(trace: ExecutionTrace) -> dict[str, Any]:
    """Serialize ``trace`` into a deterministic, JSON-safe ``dict`` for persistence or export.

    Field order follows :class:`~app.trace.models.ExecutionTrace`'s declaration order, which is
    stable across calls (Pydantic v2 preserves declared field order in ``model_dump``).
    """
    return trace.model_dump(mode="json")
