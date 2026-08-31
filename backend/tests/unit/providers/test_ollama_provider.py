"""Wire-format mapping for the local Ollama adapter (no API key, no cost)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.providers.config import ProviderConfig
from app.providers.exceptions import ProviderConnectionError
from app.providers.ollama_provider import OllamaProvider
from app.providers.schemas import ProviderMessage, ProviderRequest, ToolDefinition


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

    async def test_dropped_connection_is_mapped_to_a_clear_provider_error(self) -> None:
        """The real failure mode this reproduces: Ollama accepts the connection but crashes/OOMs
        mid-generation and closes it without ever sending a response. Previously this raw
        httpx.RemoteProtocolError escaped the provider layer entirely and surfaced to the client
        as an opaque 'An unexpected error occurred' 500 with no diagnostic (PROJECT_SPEC_2 SS47:
        adapters must raise only ProviderError subtypes, never a raw httpx exception)."""
        config = ProviderConfig(
            provider="ollama", model="llama3.1:latest", api_key="", max_retries=1
        )
        provider = OllamaProvider(config)
        await provider.initialize()

        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.post("/api/chat").mock(
                side_effect=httpx.RemoteProtocolError(
                    "Server disconnected without sending a response."
                )
            )
            with pytest.raises(ProviderConnectionError, match="closed the connection"):
                await provider.generate(
                    ProviderRequest(
                        provider="ollama",
                        model="llama3.1:latest",
                        messages=[ProviderMessage(role="user", content="hi")],
                    )
                )
        await provider.shutdown()

    async def test_other_transport_failures_are_also_mapped_not_left_raw(self) -> None:
        """Catch-all: any httpx.TransportError this adapter doesn't special-case must still
        become a ProviderConnectionError, never escape as a raw httpx exception."""
        config = ProviderConfig(
            provider="ollama", model="llama3.1:latest", api_key="", max_retries=1
        )
        provider = OllamaProvider(config)
        await provider.initialize()

        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.post("/api/chat").mock(side_effect=httpx.ReadError("connection reset"))
            with pytest.raises(ProviderConnectionError):
                await provider.generate(
                    ProviderRequest(
                        provider="ollama",
                        model="llama3.1:latest",
                        messages=[ProviderMessage(role="user", content="hi")],
                    )
                )
        await provider.shutdown()

    async def test_health_check_reports_unhealthy_when_configured_model_is_not_pulled(self) -> None:
        config = ProviderConfig(provider="ollama", model="llama3.1:latest", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.get("/api/tags").mock(
                return_value=httpx.Response(200, json={"models": [{"name": "llama2:latest"}]})
            )
            result = await provider.health_check()

        assert result.healthy is False
        assert "llama3.1:latest" in (result.message or "")
        assert "not pulled" in (result.message or "")
        await provider.shutdown()

    async def test_health_check_normalizes_a_tag_less_model_name_against_ollamas_latest_tag(
        self,
    ) -> None:
        """Ollama treats "llama3.1" as implicitly "llama3.1:latest"; GET /api/tags always returns
        the fully-tagged name, so a naive exact-string match would wrongly report a tag-less
        configured model as unavailable even though Ollama would happily serve it."""
        config = ProviderConfig(provider="ollama", model="llama3.1", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.get("/api/tags").mock(
                return_value=httpx.Response(200, json={"models": [{"name": "llama3.1:latest"}]})
            )
            result = await provider.health_check()

        assert result.healthy is True
        await provider.shutdown()

    async def test_health_check_healthy_when_model_present_with_exact_tag(self) -> None:
        config = ProviderConfig(provider="ollama", model="llama3.1:latest", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        with respx.mock(base_url="http://localhost:11434") as mock:
            mock.get("/api/tags").mock(
                return_value=httpx.Response(200, json={"models": [{"name": "llama3.1:latest"}]})
            )
            result = await provider.health_check()

        assert result.healthy is True
        await provider.shutdown()

    async def test_response_format_json_metadata_requests_ollamas_grammar_constrained_json(
        self,
    ) -> None:
        """JudgeService.submit() sets metadata={"response_format": "json"} -- the adapter must
        translate that into Ollama's own "format": "json" so a small local model reliably
        returns valid JSON instead of only being asked to via the prompt."""
        config = ProviderConfig(provider="ollama", model="llama3", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        body = {"message": {"role": "assistant", "content": "{}"}, "done": True}
        with respx.mock(base_url="http://localhost:11434") as mock:
            route = mock.post("/api/chat").mock(return_value=httpx.Response(200, json=body))
            await provider.generate(
                ProviderRequest(
                    provider="ollama",
                    model="llama3",
                    messages=[ProviderMessage(role="user", content="judge this")],
                    metadata={"response_format": "json"},
                )
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["format"] == "json"
        await provider.shutdown()

    async def test_response_format_json_is_ignored_without_the_metadata_flag(self) -> None:
        """A normal (e.g. tool-calling AUT) call must not be silently forced into JSON mode."""
        config = ProviderConfig(provider="ollama", model="llama3", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        body = {"message": {"role": "assistant", "content": "hello"}, "done": True}
        with respx.mock(base_url="http://localhost:11434") as mock:
            route = mock.post("/api/chat").mock(return_value=httpx.Response(200, json=body))
            await provider.generate(
                ProviderRequest(
                    provider="ollama",
                    model="llama3",
                    messages=[ProviderMessage(role="user", content="hi")],
                )
            )

        sent = json.loads(route.calls[0].request.content)
        assert "format" not in sent
        await provider.shutdown()

    async def test_response_format_json_is_never_set_alongside_tool_calling(self) -> None:
        """Forced JSON content mode would fight with tool-calling responses."""
        config = ProviderConfig(provider="ollama", model="llama3", api_key="")
        provider = OllamaProvider(config)
        await provider.initialize()

        body = {"message": {"role": "assistant", "content": ""}, "done": True}
        with respx.mock(base_url="http://localhost:11434") as mock:
            route = mock.post("/api/chat").mock(return_value=httpx.Response(200, json=body))
            await provider.generate(
                ProviderRequest(
                    provider="ollama",
                    model="llama3",
                    messages=[ProviderMessage(role="user", content="hi")],
                    tools=[ToolDefinition(name="search", description="search the web")],
                    metadata={"response_format": "json"},
                )
            )

        sent = json.loads(route.calls[0].request.content)
        assert "format" not in sent
        await provider.shutdown()
