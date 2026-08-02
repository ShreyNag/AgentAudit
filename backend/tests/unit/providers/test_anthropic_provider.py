"""Wire-format mapping for the Anthropic Messages API adapter."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.anthropic_provider import AnthropicProvider
from app.providers.config import ProviderConfig
from app.providers.schemas import ProviderMessage, ProviderRequest


@pytest.mark.asyncio
class TestAnthropicProvider:
    async def test_generate_parses_text_and_tool_use_blocks(self) -> None:
        config = ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="test-key")
        provider = AnthropicProvider(config)
        await provider.initialize()

        body = {
            "id": "msg_1",
            "content": [
                {"type": "text", "text": "Let me check flights."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "flight_search",
                    "input": {"origin": "NYC", "destination": "SF"},
                },
            ],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 50, "output_tokens": 10},
        }
        with respx.mock(base_url="https://api.anthropic.com/v1") as mock:
            mock.post("/messages").mock(return_value=httpx.Response(200, json=body))
            response = await provider.generate(
                ProviderRequest(
                    provider="anthropic",
                    model="claude-sonnet-5",
                    system_prompt="You are a travel agent.",
                    messages=[ProviderMessage(role="user", content="Book a flight NYC to SF")],
                )
            )

        assert response.content == "Let me check flights."
        assert response.tool_calls[0].tool_name == "flight_search"
        assert response.tool_calls[0].arguments == {"origin": "NYC", "destination": "SF"}
        assert response.usage.prompt_tokens == 50
        assert response.usage.total_tokens == 60
        await provider.shutdown()

    async def test_tool_result_message_becomes_tool_result_content_block(self) -> None:
        config = ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="test-key")
        provider = AnthropicProvider(config)
        request = ProviderRequest(
            provider="anthropic",
            model="claude-sonnet-5",
            messages=[
                ProviderMessage(role="tool", content="3 flights found", tool_call_id="toolu_1")
            ],
        )
        payload = provider._build_payload(request)
        assert payload["messages"][0]["content"][0]["type"] == "tool_result"
        assert payload["messages"][0]["content"][0]["tool_use_id"] == "toolu_1"
