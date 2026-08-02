"""Shared fixtures for Evaluation Engine unit tests."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import pytest

from app.evaluation.context import EvaluationContext
from app.evaluation.judge import JudgeService
from app.providers.base import BaseProvider
from app.providers.config import ProviderConfig
from app.providers.schemas import (
    HealthCheckResult,
    ModelInfo,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    TokenUsage,
)
from app.trace.models import ExecutionTrace


class FakeJudgeProvider(BaseProvider):
    """A BaseProvider test double that always returns a fixed, valid Judge JSON payload."""

    def __init__(self, config: ProviderConfig, payload: dict[str, object] | None = None) -> None:
        super().__init__(config)
        self.payload = payload or {
            "score": 80.0,
            "confidence": 0.9,
            "reasoning": "The agent performed well against this dimension.",
            "matched_rubric": "Strong",
            "strengths": ["followed the instruction"],
            "weaknesses": [],
            "recommendations": [],
        }
        self.call_count = 0

    async def initialize(self) -> None:
        return None

    async def validate_configuration(self) -> None:
        return None

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.call_count += 1
        return ProviderResponse(
            provider=self.config.provider, model=self.config.model, content=json.dumps(self.payload)
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        async def _gen() -> AsyncIterator[ProviderStreamEvent]:
            yield ProviderStreamEvent(is_final=True)

        return _gen()

    async def count_tokens(self, text: str, *, model: str | None = None) -> int:
        return len(text)

    async def estimate_cost(self, usage: TokenUsage, *, model: str | None = None) -> float | None:
        return None

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(provider=self.config.provider, healthy=True)

    async def list_models(self) -> list[ModelInfo]:
        return []


@pytest.fixture
def fake_judge_service() -> JudgeService:
    provider = FakeJudgeProvider(ProviderConfig(provider="openai", model="gpt-5", api_key="x"))
    return JudgeService(provider)


@pytest.fixture
def evaluation_context() -> EvaluationContext:
    trace = ExecutionTrace(
        run_uuid="run-1",
        planner={"planner_available": False},
        reasoning={"reasoning_available": False},
        messages=[{"role": "assistant", "content": "Booked flight fl-2."}],
        tool_calls=[
            {"tool_name": "book_flight", "arguments": {"flight_id": "fl-2"}, "status": "completed"}
        ],
        tool_outputs=[{"tool_name": "book_flight", "output": {"status": "confirmed"}}],
        final_response="Booked flight fl-2.",
    )
    return EvaluationContext(
        run_id=1,
        execution_trace=trace,
        task_instruction="Book the cheapest flight from NYC to SFO.",
        ground_truth={"expected_flight_id": "fl-2"},
        environment="travel",
        provider="anthropic",
        model="claude-sonnet-5",
        judge_provider="openai",
        judge_model="gpt-5",
        statistics={},
    )
