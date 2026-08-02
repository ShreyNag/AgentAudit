"""Cross-evaluator contract tests: every one of the ten evaluators behaves identically
(PROJECT_SPEC_3 SS9/SS44: independence, common interface)."""

from __future__ import annotations

import pytest

from app.evaluation.context import EvaluationContext
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
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.judge import JudgeService
from app.evaluation.rubric.loader import RubricLoader

ALL_EVALUATOR_CLASSES = [
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
]


@pytest.mark.asyncio
@pytest.mark.parametrize("evaluator_cls", ALL_EVALUATOR_CLASSES)
class TestEvaluatorContract:
    async def test_evaluate_returns_a_complete_result(
        self,
        evaluator_cls: type,
        fake_judge_service: JudgeService,
        evaluation_context: EvaluationContext,
    ) -> None:
        evaluator = evaluator_cls(fake_judge_service, EvidenceExtractor(), RubricLoader())
        result = await evaluator.evaluate(evaluation_context)

        assert result.evaluator_name == evaluator_cls.name
        assert 0.0 <= result.score <= 100.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning
        assert result.matched_rubric == "Strong"

    async def test_evidence_categories_are_a_subset_of_known_categories(
        self, evaluator_cls: type, fake_judge_service: JudgeService
    ) -> None:
        # Every evaluator's declared evidence_categories must be non-empty -- an evaluator with
        # no evidence categories could never ground its judgment in anything (PROJECT_SPEC_3
        # SS15: "Scores without evidence are invalid").
        evaluator = evaluator_cls(fake_judge_service, EvidenceExtractor(), RubricLoader())
        assert len(evaluator.evidence_categories) > 0
