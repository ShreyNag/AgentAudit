"""Shared fixtures for Execution Engine unit tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

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


class FakeSequentialProvider(BaseProvider):
    """A BaseProvider test double that replays a fixed sequence of responses.

    Each call to :meth:`generate` returns the next response in ``responses``; the last
    response is repeated indefinitely if the sequence is exhausted (guards against infinite
    test loops producing an IndexError instead of a clear assertion failure).
    """

    def __init__(self, config: ProviderConfig, responses: list[ProviderResponse]) -> None:
        super().__init__(config)
        self.responses = responses
        self.call_count = 0

    async def initialize(self) -> None:
        return None

    async def validate_configuration(self) -> None:
        return None

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        index = min(self.call_count, len(self.responses) - 1)
        self.call_count += 1
        return self.responses[index]

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
def fake_provider_config() -> ProviderConfig:
    return ProviderConfig(provider="fake", model="fake-model", api_key="x")
