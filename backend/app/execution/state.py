"""``ExecutionState`` (PROJECT_SPEC_6 SS38): mutable runtime information for one execution."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from app.providers.schemas import ProviderMessage


@dataclass
class ExecutionState:
    """Tracks the mutable, in-progress state of a single execution."""

    status: str = "initialized"
    current_step: int = 0
    iteration_count: int = 0
    tool_call_count: int = 0
    messages: list[ProviderMessage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    completed: bool = False
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
