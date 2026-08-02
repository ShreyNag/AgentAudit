"""``EvaluationEngine`` full pipeline (PROJECT_SPEC_6 SS64-65)."""

from __future__ import annotations

import pytest

from app.core.constants import EVALUATOR_NAMES
from app.evaluation.behaviour_classifier import BehaviourClassifier
from app.evaluation.context import EvaluationContext
from app.evaluation.engine import EvaluationEngine
from app.evaluation.evaluators.registry import build_default_registry
from app.evaluation.evidence_extractor import EvidenceExtractor
from app.evaluation.failure_attribution import FailureAttributionEngine
from app.evaluation.judge import JudgeService
from app.evaluation.rubric.loader import RubricLoader
from app.evaluation.scoring.cts import CTSCalculator


@pytest.mark.asyncio
class TestEvaluationEngine:
    async def test_run_produces_all_ten_evaluator_results_and_a_cts(
        self, fake_judge_service: JudgeService, evaluation_context: EvaluationContext
    ) -> None:
        engine = EvaluationEngine(
            build_default_registry(),
            BehaviourClassifier(),
            FailureAttributionEngine(),
            CTSCalculator(),
            EvidenceExtractor(),
            RubricLoader(),
        )
        outcome = await engine.run(evaluation_context, fake_judge_service)

        assert {r.evaluator_name for r in outcome.evaluator_results} == set(EVALUATOR_NAMES)
        assert outcome.cts.cts == pytest.approx(80.0)  # every fake score is 80.0
        assert outcome.behaviour.classification == "SAFE_CORRECT"
        assert outcome.failure is None  # no evaluator fell below the failure threshold

    async def test_evaluators_run_independently_even_if_the_provider_is_slow(
        self, fake_judge_service: JudgeService, evaluation_context: EvaluationContext
    ) -> None:
        engine = EvaluationEngine(
            build_default_registry(),
            BehaviourClassifier(),
            FailureAttributionEngine(),
            CTSCalculator(),
            EvidenceExtractor(),
            RubricLoader(),
        )
        await engine.run(evaluation_context, fake_judge_service)
        provider = fake_judge_service.provider
        assert provider.call_count == len(EVALUATOR_NAMES)  # one Judge call per evaluator
