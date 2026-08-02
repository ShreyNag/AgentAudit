"""``EvaluatorRegistry`` (PROJECT_SPEC_6 SS68): evaluator discovery, ordering, and execution.

Evaluators run independently (PROJECT_SPEC_1 Principle 2, PROJECT_SPEC_3 SS9/SS44) -- executed
concurrently via ``asyncio.gather`` here, matching PROJECT_SPEC_6 SS123's "parallel evaluator
execution" as a present capability rather than a future one, since independence makes it safe.
"""

from __future__ import annotations

import asyncio

from app.evaluation.context import EvaluationContext
from app.evaluation.evaluators.base import BaseEvaluator
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.judge import JudgeService
from app.evaluation.models import EvaluationResult
from app.evaluation.rubric.loader import RubricLoader


class EvaluatorRegistry:
    """Registry of evaluator classes, in their configured execution order."""

    def __init__(self) -> None:
        """Start with an empty registry; evaluators register via :meth:`register`."""
        self._factories: dict[str, type[BaseEvaluator]] = {}
        self._order: list[str] = []

    def register(self, evaluator_cls: type[BaseEvaluator]) -> None:
        """Register ``evaluator_cls``, appending it to the execution order if new."""
        self._factories[evaluator_cls.name] = evaluator_cls
        if evaluator_cls.name not in self._order:
            self._order.append(evaluator_cls.name)

    def list_evaluators(self) -> list[str]:
        """Return every registered evaluator name, in execution order."""
        return list(self._order)

    def _build_instances(
        self,
        judge: JudgeService,
        evidence_extractor: EvidenceExtractor,
        rubric_loader: RubricLoader,
    ) -> list[BaseEvaluator]:
        return [
            self._factories[name](judge, evidence_extractor, rubric_loader) for name in self._order
        ]

    async def run_all(
        self,
        context: EvaluationContext,
        *,
        judge: JudgeService,
        evidence_extractor: EvidenceExtractor,
        rubric_loader: RubricLoader,
    ) -> list[EvaluationResult]:
        """Run every registered evaluator concurrently and return their results.

        No evaluator's outcome depends on another's -- a failure in one evaluator's Judge call
        does not prevent the others from completing.
        """
        evaluators = self._build_instances(judge, evidence_extractor, rubric_loader)
        results = await asyncio.gather(*(evaluator.evaluate(context) for evaluator in evaluators))
        return list(results)


def build_default_registry() -> EvaluatorRegistry:
    """Build the standard registry with all ten evaluators, in PROJECT_SPEC_3 SS8's order."""
    from app.evaluation.evaluators.alignment import AlignmentEvaluator
    from app.evaluation.evaluators.instruction_integrity import InstructionIntegrityEvaluator
    from app.evaluation.evaluators.integrity import IntegrityEvaluator
    from app.evaluation.evaluators.memory import MemoryEvaluator
    from app.evaluation.evaluators.planner import PlannerEvaluator
    from app.evaluation.evaluators.security import SecurityEvaluator
    from app.evaluation.evaluators.tool_correctness import ToolCorrectnessEvaluator
    from app.evaluation.evaluators.tool_faithfulness import ToolFaithfulnessEvaluator
    from app.evaluation.evaluators.tool_invocation import ToolInvocationEvaluator
    from app.evaluation.evaluators.tool_selection import ToolSelectionEvaluator

    registry = EvaluatorRegistry()
    for evaluator_cls in (
        InstructionIntegrityEvaluator,
        PlannerEvaluator,
        MemoryEvaluator,
        ToolSelectionEvaluator,
        ToolInvocationEvaluator,
        ToolCorrectnessEvaluator,
        AlignmentEvaluator,
        ToolFaithfulnessEvaluator,
        SecurityEvaluator,
        IntegrityEvaluator,
    ):
        registry.register(evaluator_cls)
    return registry
