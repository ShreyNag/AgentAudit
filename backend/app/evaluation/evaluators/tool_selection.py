"""Tool Selection Evaluator (PROJECT_SPEC_3 SS34)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class ToolSelectionEvaluator(BaseEvaluator):
    """Evaluates whether appropriate tools were selected, independent of execution quality."""

    name = "tool_selection"
    description = "Evaluates whether the AUT chose the correct, minimal, well-ordered tool set."
    evidence_categories = ["planner", "tool_sequence", "ground_truth"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate only tool *selection*: was the correct tool chosen for the task, were "
            "unnecessary tools avoided, was ordering correct, was the correct environment's "
            "toolset used, were any required tools omitted, and were any calls redundant? Do "
            "not evaluate whether the tool arguments or outputs were handled correctly -- only "
            "whether the right tools were chosen."
        )
