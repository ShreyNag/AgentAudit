"""Retry-on-transient-failure and HTTP-status -> typed-exception mapping.

PROJECT_SPEC_2 SS40/47.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.config import ProviderConfig
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderValidationError,
)
from app.providers.openai_provider import OpenAIProvider
from app.providers.schemas import ProviderMessage, ProviderRequest


@pytest.mark.asyncio
class TestRetryAndErrorNormalization:
    async def test_401_maps_to_authentication_error_without_retrying(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="bad-key", max_retries=3)
        provider = OpenAIProvider(config)
        await provider.initialize()

        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            route = mock.post("/chat/completions").mock(
                return_value=httpx.Response(401, json={"error": "invalid api key"})
            )
            with pytest.raises(ProviderAuthenticationError):
                await provider.generate(
                    ProviderRequest(
                        provider="openai",
                        model="gpt-5",
                        messages=[ProviderMessage(role="user", content="hi")],
                    )
                )
        # Not a retriable error type, so exactly one attempt should have been made.
        assert route.call_count == 1
        await provider.shutdown()

    async def test_400_maps_to_validation_error(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="test-key")
        provider = OpenAIProvider(config)
        await provider.initialize()

        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            mock.post("/chat/completions").mock(
                return_value=httpx.Response(400, json={"error": "bad request"})
            )
            with pytest.raises(ProviderValidationError):
                await provider.generate(
                    ProviderRequest(
                        provider="openai",
                        model="gpt-5",
                        messages=[ProviderMessage(role="user", content="hi")],
                    )
                )
        await provider.shutdown()

    async def test_429_is_retried_up_to_max_retries_then_raises(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="test-key", max_retries=2)
        provider = OpenAIProvider(config)
        await provider.initialize()

        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            route = mock.post("/chat/completions").mock(
                return_value=httpx.Response(429, json={"error": "rate limited"})
            )
            with pytest.raises(ProviderRateLimitError):
                await provider.generate(
                    ProviderRequest(
                        provider="openai",
                        model="gpt-5",
                        messages=[ProviderMessage(role="user", content="hi")],
                    )
                )
        assert route.call_count == 2  # exactly max_retries attempts, then it gives up
        await provider.shutdown()

    async def test_success_after_one_rate_limit_retry(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="test-key", max_retries=3)
        provider = OpenAIProvider(config)
        await provider.initialize()

        responses = [
            httpx.Response(429, json={"error": "rate limited"}),
            httpx.Response(
                200,
                json={
                    "id": "ok",
                    "choices": [
                        {
                            "message": {"role": "assistant", "content": "done"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            ),
        ]
        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            mock.post("/chat/completions").mock(side_effect=responses)
            response = await provider.generate(
                ProviderRequest(
                    provider="openai",
                    model="gpt-5",
                    messages=[ProviderMessage(role="user", content="hi")],
                )
            )
        assert response.content == "done"
        await provider.shutdown()
