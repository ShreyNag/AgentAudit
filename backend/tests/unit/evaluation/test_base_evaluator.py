"""``BaseEvaluator`` template-method behavior (docs/adr/0008-*.md), tested via a concrete subclass.

Uses ``ToolInvocationEvaluator`` specifically because its evidence categories (``tool_calls``,
``errors``) are the only ones that can genuinely be empty -- every other evaluator also
requests at least one context-derived category (``planner``, ``reasoning``, ``instructions``,
etc.) that always yields exactly one evidence item regardless of trace content.
"""

from __future__ import annotations

import pytest

from app.evaluation.context import EvaluationContext
from app.evaluation.evaluators.tool_invocation import ToolInvocationEvaluator
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.judge import JudgeService
from app.evaluation.rubric.loader import RubricLoader
from app.trace.models import ExecutionTrace


@pytest.mark.asyncio
class TestBaseEvaluatorConfidenceAdjustment:
    async def test_confidence_is_penalized_when_no_evidence_is_extracted(
        self, fake_judge_service: JudgeService
    ) -> None:
        empty_context = EvaluationContext(
            run_id=1,
            execution_trace=ExecutionTrace(run_uuid="run-empty"),  # no tool_calls, no errors
            task_instruction="Book a flight.",
            ground_truth={},
            environment="travel",
            provider="anthropic",
            model="claude-sonnet-5",
            judge_provider="openai",
            judge_model="gpt-5",
            statistics={},
        )
        evaluator = ToolInvocationEvaluator(fake_judge_service, EvidenceExtractor(), RubricLoader())
        result = await evaluator.evaluate(empty_context)

        # The fake judge always reports confidence=0.9; with zero evidence it must be halved
        # (PROJECT_SPEC_3 SS19/SS68: "missing information lowers confidence").
        assert result.evidence == []
        assert result.confidence == pytest.approx(0.45)

    async def test_confidence_is_unaffected_when_evidence_is_present(
        self, fake_judge_service: JudgeService, evaluation_context: EvaluationContext
    ) -> None:
        evaluator = ToolInvocationEvaluator(fake_judge_service, EvidenceExtractor(), RubricLoader())
        result = await evaluator.evaluate(evaluation_context)
        assert len(result.evidence) > 0
        assert result.confidence == pytest.approx(0.9)
