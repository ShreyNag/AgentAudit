"""``JudgeService`` prompt construction and output validation (PROJECT_SPEC_3 SS102-108)."""

from __future__ import annotations

import json

import pytest

from app.core.exceptions import EvaluationError
from app.evaluation.context import EvaluationContext
from app.evaluation.judge import JudgeService
from app.evaluation.rubric.loader import RubricLoader
from app.providers.config import ProviderConfig
from app.providers.schemas import ProviderResponse
from tests.unit.execution.conftest import FakeSequentialProvider


def _context() -> EvaluationContext:
    from app.trace.models import ExecutionTrace

    return EvaluationContext(
        run_id=1,
        execution_trace=ExecutionTrace(run_uuid="run-1"),
        task_instruction="Book a flight.",
        ground_truth={"expected_flight_id": "fl-2"},
        environment="travel",
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="openai",
        judge_model="gpt-5",
        statistics={},
    )


@pytest.fixture
def judge() -> JudgeService:
    provider = FakeSequentialProvider(
        ProviderConfig(provider="openai", model="gpt-5", api_key="x"), []
    )
    return JudgeService(provider)


class TestJudgeServicePromptBuilding:
    def test_build_prompt_includes_rubric_criteria_and_evidence(self, judge: JudgeService) -> None:
        rubric = RubricLoader().get("security")
        system, user = judge.build_prompt(
            evaluator_name="security",
            evaluator_instructions="Focus on prompt injection.",
            rubric=rubric,
            context=_context(),
            evidence=[],
        )
        assert "security" in system
        assert rubric.criteria[0] in user
        assert "no evidence extracted" in user


class TestJudgeServiceResponseValidation:
    def test_valid_json_response_is_parsed(self, judge: JudgeService) -> None:
        payload = {
            "score": 8.5,
            "confidence": 0.9,
            "reasoning": "Solid execution.",
            "matched_rubric": "Strong",
            "strengths": ["followed constraints"],
            "weaknesses": [],
            "recommendations": [],
        }
        response = ProviderResponse(provider="openai", model="gpt-5", content=json.dumps(payload))
        parsed = judge.validate_response(response)
        assert parsed["score"] == 8.5
        assert parsed["matched_rubric"] == "Strong"

    def test_markdown_fenced_json_is_still_parsed(self, judge: JudgeService) -> None:
        payload = {"score": 7.0, "confidence": 0.8, "reasoning": "ok"}
        content = f"```json\n{json.dumps(payload)}\n```"
        response = ProviderResponse(provider="openai", model="gpt-5", content=content)
        parsed = judge.validate_response(response)
        assert parsed["score"] == 7.0

    def test_invalid_json_raises_evaluation_error(self, judge: JudgeService) -> None:
        response = ProviderResponse(provider="openai", model="gpt-5", content="not json at all")
        with pytest.raises(EvaluationError):
            judge.validate_response(response)

    def test_missing_required_field_raises_evaluation_error(self, judge: JudgeService) -> None:
        response = ProviderResponse(
            provider="openai", model="gpt-5", content=json.dumps({"score": 5.0})
        )
        with pytest.raises(EvaluationError):
            judge.validate_response(response)

    def test_out_of_range_score_is_clamped(self, judge: JudgeService) -> None:
        payload = {"score": 150.0, "confidence": 1.5, "reasoning": "x"}
        response = ProviderResponse(provider="openai", model="gpt-5", content=json.dumps(payload))
        parsed = judge.validate_response(response)
        assert parsed["score"] == 100.0
        assert parsed["confidence"] == 1.0
