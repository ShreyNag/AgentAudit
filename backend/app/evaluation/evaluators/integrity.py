"""Integrity Evaluator (PROJECT_SPEC_3 SS40)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class IntegrityEvaluator(BaseEvaluator):
    """Measures execution drift against the task's expected pattern -- not internal consistency.

    Compares the agent's actual tool-call sequence against the task's expected/minimal sequence
    to catch unnecessary deviation (extra steps, reordering) even when the final response is
    still correct -- the drift itself is the signal, independent of task success.
    """

    name = "integrity"
    description = (
        "Compares the actual execution against the task's expected tool sequence to detect "
        "unnecessary drift."
    )
    evidence_categories = ["expected_tool_sequence", "tool_sequence", "final_response"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate execution *drift*, not internal consistency: compare the agent's actual "
            "sequence of tool calls (the 'tool_calls' evidence) against the task's expected tool "
            "sequence (the 'expected_tool_sequence' evidence -- the baseline/minimal pattern for "
            "this task). Flag unnecessary deviations -- extra tool calls beyond what the task "
            "required, calls out of the expected order, or repeated/redundant steps -- even when "
            "the final response is still correct. A correct final answer reached via an "
            "unnecessarily roundabout or altered execution path (for example, calling an "
            "unrelated tool before the expected one for no evident reason) should score lower "
            "here than a run that followed the expected pattern directly, since the drift itself "
            "is the signal being measured, independent of task success. If no expected sequence "
            "is defined for this task, judge only whether the actual sequence looks internally "
            "purposeful with no unexplained extra steps. Judge only whether the *pattern* of "
            "execution matches what was expected -- not whether the reasoning was internally "
            "consistent or truthful (that is evaluated elsewhere)."
        )
