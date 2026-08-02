"""Wire-format mapping for the Google Gemini ``generateContent`` adapter."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.config import ProviderConfig
from app.providers.gemini_provider import GeminiProvider
from app.providers.schemas import ProviderMessage, ProviderRequest


@pytest.mark.asyncio
class TestGeminiProvider:
    async def test_generate_parses_function_call_parts(self) -> None:
        config = ProviderConfig(provider="gemini", model="gemini-2.5-pro", api_key="test-key")
        provider = GeminiProvider(config)
        await provider.initialize()

        body = {
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [
                            {"functionCall": {"name": "flight_search", "args": {"origin": "NYC"}}}
                        ],
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 30,
                "candidatesTokenCount": 8,
                "totalTokenCount": 38,
            },
        }
        with respx.mock(base_url="https://generativelanguage.googleapis.com/v1beta") as mock:
            mock.post("/models/gemini-2.5-pro:generateContent").mock(
                return_value=httpx.Response(200, json=body)
            )
            response = await provider.generate(
                ProviderRequest(
                    provider="gemini",
                    model="gemini-2.5-pro",
                    messages=[ProviderMessage(role="user", content="Find a flight from NYC")],
                )
            )

        assert response.tool_calls[0].tool_name == "flight_search"
        assert response.usage.total_tokens == 38
        await provider.shutdown()

    def test_assistant_role_maps_to_model_role(self) -> None:
        config = ProviderConfig(provider="gemini", model="gemini-2.5-pro", api_key="test-key")
        provider = GeminiProvider(config)
        request = ProviderRequest(
            provider="gemini",
            model="gemini-2.5-pro",
            messages=[ProviderMessage(role="assistant", content="Sure, one moment.")],
        )
        contents = provider._build_contents(request)
        assert contents[0]["role"] == "model"
