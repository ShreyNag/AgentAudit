"""Wire-format mapping for the local Ollama adapter (no API key, no cost)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.config import ProviderConfig
from app.providers.ollama_provider import OllamaProvider
from app.providers.schemas import ProviderMessage, ProviderRequest


@pytest.mark.asyncio
class TestOllamaProvider:
    async def test_generate_parses_local_chat_response(self) -> None:
        config = ProviderConfig(provider="ollama", model="llama3", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        body = {
            "message": {"role": "assistant", "content": "Hello from Llama."},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 6,
        }
        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.post("/api/chat").mock(return_value=httpx.Response(200, json=body))
            response = await provider.generate(
                ProviderRequest(
                    provider="ollama",
                    model="llama3",
                    messages=[ProviderMessage(role="user", content="hi")],
                )
            )

        assert response.content == "Hello from Llama."
        assert response.usage.total_tokens == 18
        assert response.usage.estimated_cost is None
        await provider.shutdown()

    async def test_ollama_requires_no_api_key(self) -> None:
        config = ProviderConfig(provider="ollama", model="llama3", api_key="")
        provider = OllamaProvider(config)
        await provider.validate_configuration()  # must not raise despite empty api_key
