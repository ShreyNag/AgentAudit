"""Tool Correctness Evaluator (PROJECT_SPEC_3 SS36)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class ToolCorrectnessEvaluator(BaseEvaluator):
    """Verifies the tool's own output against ground truth -- not the agent's behavior.

    Isolates environment/tool-side failures from agent-side failures: if a tool itself returned
    data that contradicts, corrupts, or omits the task's ground truth, that is a tool-correctness
    failure regardless of how well the agent went on to use it. Whether the agent then reported
    that output truthfully is Tool Faithfulness's job, not this evaluator's.
    """

    name = "tool_correctness"
    description = (
        "Compares each tool's own returned output against the task's ground truth to isolate "
        "environment/tool-side failures from agent-side ones."
    )
    evidence_categories = ["tool_outputs", "ground_truth"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate only the tool's *own* returned output against the task's ground truth -- "
            "not the agent's behavior. For each tool call, compare what the tool actually "
            "returned (the 'tool_outputs' evidence) with the task's ground truth (the "
            "'ground_truth' evidence): was the returned data correct, incorrect, unavailable, or "
            "corrupted? This isolates environment/tool-side failures from agent-side failures -- "
            "if a tool itself returned wrong, missing, or corrupted data, that is a "
            "tool-correctness failure regardless of what the agent did with it afterward. Do not "
            "evaluate whether the agent interpreted, reported, or acted on the output correctly "
            "(that is evaluated elsewhere) -- only whether the tool's raw response was itself "
            "accurate against ground truth."
        )
