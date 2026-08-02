"""Tool Invocation Evaluator (PROJECT_SPEC_3 SS35)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class ToolInvocationEvaluator(BaseEvaluator):
    """Evaluates invocation quality: parameters, validation, retries -- not tool correctness."""

    name = "tool_invocation"
    description = "Evaluates parameter correctness, completeness, and invocation consistency."
    evidence_categories = ["tool_calls", "errors"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate only how correctly tools were *invoked*: were parameters correct and "
            "complete, was input validated, was invocation timing sensible, and was retry "
            "behavior appropriate after failures? Do not evaluate whether the chosen tool was "
            "the right one, or whether its output was correctly interpreted afterward."
        )
