"""Default method behavior on ``BaseProvider`` (ADR-002): chat/reason delegate to generate."""

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


class _FakeProvider(BaseProvider):
    """Minimal concrete BaseProvider used only to exercise the shared default methods."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.generate_calls = 0
        self.shutdown_called = False

    async def initialize(self) -> None:
        return None

    async def validate_configuration(self) -> None:
        return None

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.generate_calls += 1
        return ProviderResponse(
            provider=self.config.provider, model=self.config.model, content="ok"
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        async def _gen() -> AsyncIterator[ProviderStreamEvent]:
            yield ProviderStreamEvent(delta="ok", is_final=True)

        return _gen()

    async def count_tokens(self, text: str, *, model: str | None = None) -> int:
        return len(text)

    async def estimate_cost(self, usage: TokenUsage, *, model: str | None = None) -> float | None:
        return None

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(provider=self.config.provider, healthy=True)

    async def list_models(self) -> list[ModelInfo]:
        return []

    async def shutdown(self) -> None:
        self.shutdown_called = True


@pytest.fixture
def fake_provider() -> _FakeProvider:
    return _FakeProvider(ProviderConfig(provider="fake", model="fake-model", api_key="x"))


@pytest.mark.asyncio
class TestBaseProviderDefaults:
    async def test_chat_delegates_to_generate(self, fake_provider: _FakeProvider) -> None:
        request = ProviderRequest(provider="fake", model="fake-model", messages=[])
        response = await fake_provider.chat(request)
        assert response.content == "ok"
        assert fake_provider.generate_calls == 1

    async def test_reason_delegates_to_generate(self, fake_provider: _FakeProvider) -> None:
        request = ProviderRequest(provider="fake", model="fake-model", messages=[])
        await fake_provider.reason(request)
        assert fake_provider.generate_calls == 1

    async def test_close_is_an_alias_for_shutdown(self, fake_provider: _FakeProvider) -> None:
        await fake_provider.close()
        assert fake_provider.shutdown_called is True

    async def test_stream_yields_normalized_events(self, fake_provider: _FakeProvider) -> None:
        request = ProviderRequest(provider="fake", model="fake-model", messages=[])
        events = [event async for event in fake_provider.stream(request)]
        assert events[0].is_final is True
