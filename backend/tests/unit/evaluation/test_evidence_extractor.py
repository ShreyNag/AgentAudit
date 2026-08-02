"""``EvidenceExtractor`` (PROJECT_SPEC_6 SS71-72)."""

from __future__ import annotations

from app.evaluation.context import EvaluationContext
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.trace.models import ExecutionTrace


def _make_context(**trace_overrides: object) -> EvaluationContext:
    trace = ExecutionTrace(run_uuid="run-1", **trace_overrides)  # type: ignore[arg-type]
    return EvaluationContext(
        run_id=1,
        execution_trace=trace,
        task_instruction="Book a flight.",
        ground_truth={"expected_flight_id": "fl-2"},
        environment="travel",
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="openai",
        judge_model="gpt-5",
        statistics={},
    )


class TestEvidenceExtractor:
    def test_extracts_tool_calls_as_evidence(self) -> None:
        context = _make_context(tool_calls=[{"tool_name": "book_flight", "status": "completed"}])
        evidence = EvidenceExtractor().extract(context, ["tool_calls"])
        assert len(evidence) == 1
        assert evidence[0].category == "tool_calls"

    def test_failed_tool_call_is_marked_as_warning_severity(self) -> None:
        context = _make_context(tool_calls=[{"tool_name": "book_flight", "status": "failed"}])
        evidence = EvidenceExtractor().extract(context, ["tool_calls"])
        assert evidence[0].severity == "warning"

    def test_ground_truth_and_instructions_come_from_context_not_trace(self) -> None:
        context = _make_context()
        evidence = EvidenceExtractor().extract(context, ["ground_truth", "instructions"])
        categories = {item.category for item in evidence}
        assert categories == {"ground_truth", "instructions"}

    def test_missing_final_response_is_flagged_as_warning(self) -> None:
        context = _make_context(final_response=None)
        evidence = EvidenceExtractor().extract(context, ["final_response"])
        assert evidence[0].severity == "warning"

    def test_unrequested_categories_produce_no_evidence(self) -> None:
        context = _make_context(errors=["boom"])
        evidence = EvidenceExtractor().extract(context, ["planner"])
        assert all(item.category == "planner" for item in evidence)
