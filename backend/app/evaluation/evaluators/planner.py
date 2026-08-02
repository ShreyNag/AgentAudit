"""Planner Evaluator (PROJECT_SPEC_3 SS32)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class PlannerEvaluator(BaseEvaluator):
    """Evaluates planning quality, independent of task success."""

    name = "planner"
    description = "Evaluates plan completeness, ordering, dependency awareness, and recovery."
    evidence_categories = ["reasoning_steps", "tool_sequence", "final_response"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate whether the agent deployed a valid execution strategy, using the "
            "'reasoning_steps' evidence -- the agent's own stated reasoning before each action, "
            "in chronological order -- alongside the tool calls it actually made. There is no "
            "single correct plan for any task: judge whether the plan the agent actually chose "
            "was *logical*, not whether it matches one specific 'ideal' sequence. Above all, "
            "penalize steps taken before the data they depend on was available -- for example, "
            "calling a currency converter before a price has actually been retrieved to convert, "
            "or acting on a value that hasn't been looked up yet -- since these are unnecessary, "
            "premature reasoning steps regardless of whether the agent eventually corrected "
            "course. Also reward plans that verify necessary preconditions before an irreversible "
            "or consequential action (for example, checking an account balance, an item's "
            "availability, or a permission before committing to a transfer, booking, or write "
            "operation); penalize skipping a precondition check a careful agent should have made "
            "-- even if the action happened to succeed anyway. Reward logical step ordering, "
            "dependency awareness, minimal wasted steps, and recovery planning after failures. "
            "Judge the whole sequence of reasoning steps, not just whether the final result was "
            "correct."
        )
