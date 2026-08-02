"""Trace event types (PROJECT_SPEC_1 SS57, PROJECT_SPEC_6 SS52).

New event types may be added without modifying existing ones (PROJECT_SPEC_2 SS80).
"""

from __future__ import annotations

from enum import StrEnum


class TraceEventType(StrEnum):
    """Every kind of event the Trace Recorder can append to an execution trace."""

    RUN_STARTED = "RunStarted"
    TASK_LOADED = "TaskLoaded"
    PLANNER_STEP = "PlannerStep"
    PROVIDER_REQUEST = "ProviderRequest"
    PROVIDER_RESPONSE = "ProviderResponse"
    REASONING_GENERATED = "ReasoningGenerated"
    TOOL_SELECTED = "ToolSelected"
    TOOL_INVOKED = "ToolInvoked"
    TOOL_COMPLETED = "ToolCompleted"
    TOOL_FAILED = "ToolFailed"
    OBSERVATION_RECORDED = "ObservationRecorded"
    MEMORY_RETRIEVED = "MemoryRetrieved"
    MEMORY_UPDATED = "MemoryUpdated"
    ENVIRONMENT_UPDATED = "EnvironmentUpdated"
    WARNING = "Warning"
    ERROR = "Error"
    FINAL_RESPONSE_PRODUCED = "FinalResponseProduced"
    REFLECTION_RECORDED = "ReflectionRecorded"
    RUN_COMPLETED = "RunCompleted"
    RUN_FAILED = "RunFailed"
