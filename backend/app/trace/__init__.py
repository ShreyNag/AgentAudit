"""Trace System (PROJECT_SPEC_1 Part 3, PROJECT_SPEC_6 SS51-58): the backbone of AgentAudit.

The Trace Recorder passively records execution and never modifies it (PROJECT_SPEC_2 SS78).
Nothing in this package imports from :mod:`app.evaluation` -- execution and evaluation remain
fully decoupled (PROJECT_SPEC_1 SS106).
"""

from app.trace.events import TraceEventType
from app.trace.models import ExecutionTrace
from app.trace.recorder import TraceRecorder
from app.trace.replay import ReplayLoader
from app.trace.serializer import serialize_trace

__all__ = [
    "TraceEventType",
    "ExecutionTrace",
    "TraceRecorder",
    "ReplayLoader",
    "serialize_trace",
]
