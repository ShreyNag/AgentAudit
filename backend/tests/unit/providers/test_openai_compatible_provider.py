"""Wire-format mapping for the OpenAI Chat Completions family (OpenAI/Groq/DeepSeek adapters)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.config import ProviderConfig
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.sarvam_provider import SarvamProvider
from app.providers.schemas import ProviderMessage, ProviderRequest, ToolDefinition

_CHAT_COMPLETION_BODY = {
    "id": "chatcmpl-123",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "flight_search",
                            "arguments": '{"origin": "NYC", "destination": "SF"}',
                        },
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
}


@pytest.mark.asyncio
class TestOpenAICompatibleProvider:
    async def test_generate_parses_tool_calls_and_usage(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="test-key")
        provider = OpenAIProvider(config)
        await provider.initialize()

        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            mock.post("/chat/completions").mock(
                return_value=httpx.Response(200, json=_CHAT_COMPLETION_BODY)
            )
            response = await provider.generate(
                ProviderRequest(
                    provider="openai",
                    model="gpt-5",
                    messages=[ProviderMessage(role="user", content="Find me a flight NYC to SF")],
                    tools=[
                        ToolDefinition(
                            name="flight_search",
                            description="Search flights",
                            parameters={"type": "object", "properties": {}},
                        )
                    ],
                )
            )

        assert response.tool_calls[0].tool_name == "flight_search"
        assert response.tool_calls[0].arguments == {"origin": "NYC", "destination": "SF"}
        assert response.usage.prompt_tokens == 100
        assert response.usage.estimated_cost is not None
        assert response.finish_reason == "tool_calls"
        await provider.shutdown()

    async def test_deepseek_surfaces_reasoning_content(self) -> None:
        config = ProviderConfig(provider="deepseek", model="deepseek-reasoner", api_key="test-key")
        provider = DeepSeekProvider(config)
        await provider.initialize()

        body = {
            "id": "1",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The answer is 4.",
                        "reasoning_content": "2 + 2 = 4.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        with respx.mock(base_url="https://api.deepseek.com") as mock:
            mock.post("/chat/completions").mock(return_value=httpx.Response(200, json=body))
            response = await provider.generate(
                ProviderRequest(
                    provider="deepseek",
                    model="deepseek-reasoner",
                    messages=[ProviderMessage(role="user", content="What is 2+2?")],
                )
            )

        assert response.reasoning_available is True
        assert response.reasoning == "2 + 2 = 4."
        await provider.shutdown()

    async def test_sarvam_parses_chat_completions_like_any_other_openai_compatible_vendor(
        self,
    ) -> None:
        config = ProviderConfig(provider="sarvam", model="sarvam-105b", api_key="test-key")
        provider = SarvamProvider(config)
        await provider.initialize()

        body = {
            "id": "1",
            "choices": [
                {"message": {"role": "assistant", "content": "Namaste!"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }
        with respx.mock(base_url="https://api.sarvam.ai/v1") as mock:
            mock.post("/chat/completions").mock(return_value=httpx.Response(200, json=body))
            response = await provider.generate(
                ProviderRequest(
                    provider="sarvam",
                    model="sarvam-105b",
                    messages=[ProviderMessage(role="user", content="Hello")],
                )
            )

        assert response.content == "Namaste!"
        assert response.usage.total_tokens == 8
        await provider.shutdown()

    async def test_health_check_uses_models_endpoint_not_a_chat_call(self) -> None:
        config = ProviderConfig(provider="openai", model="gpt-5", api_key="test-key")
        provider = OpenAIProvider(config)
        await provider.initialize()

        with respx.mock(base_url="https://api.openai.com/v1") as mock:
            models_route = mock.get("/models").mock(
                return_value=httpx.Response(200, json={"data": [{"id": "gpt-5"}]})
            )
            result = await provider.health_check()

        assert models_route.called
        assert result.healthy is True
        await provider.shutdown()
