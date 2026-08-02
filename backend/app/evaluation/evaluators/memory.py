"""Memory Evaluator (PROJECT_SPEC_3 SS33)."""

from __future__ import annotations

from app.evaluation.evaluators.base import BaseEvaluator


class MemoryEvaluator(BaseEvaluator):
    """Evaluates correctness and relevance of memory usage."""

    name = "memory"
    description = "Evaluates retrieval correctness, relevant usage, and memory consistency."
    evidence_categories = ["messages", "reasoning"]

    def evaluator_instructions(self) -> str:
        return (
            "Evaluate the agent's use of memory (conversation history, retrieved context): was "
            "retrieval correct, was usage relevant, was any memory or context hallucinated, and "
            "was context retained consistently across turns? This evaluator exists to *isolate* "
            "memory-retrieval failures from planning or tool-execution failures: if the agent "
            "retrieved the wrong stored item (for example, the wrong hotel or record from an "
            "earlier turn) but its planning and tool calls then executed correctly on that wrong "
            "item, the failure belongs here, not to the Planner or Tool evaluators -- score this "
            "dimension low even though the rest of the execution looked competent, since the "
            "final result was wrong specifically because of what was retrieved. Conversely, if "
            "retrieval was correct and a later stage of execution went wrong, this dimension "
            "should still score well. If the evidence shows no distinct memory subsystem beyond "
            "conversation history, evaluate context retention within that conversation instead "
            "of penalizing the absence of external memory."
        )
