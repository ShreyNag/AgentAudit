"""``serialize_trace`` (PROJECT_SPEC_2 SS81): deterministic, JSON-safe output."""

from __future__ import annotations

from app.trace.models import ExecutionTrace
from app.trace.serializer import serialize_trace


class TestSerializeTrace:
    def test_serialize_trace_is_json_safe_and_deterministic(self) -> None:
        trace = ExecutionTrace(run_uuid="run-1", final_response="done")
        first = serialize_trace(trace)
        second = serialize_trace(trace)
        assert first == second
        assert first["run_uuid"] == "run-1"
        assert list(first.keys())[0] == "run_uuid"  # stable field ordering
