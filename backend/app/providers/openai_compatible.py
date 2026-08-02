"""Shared request/response mapping for OpenAI Chat-Completions-compatible APIs.

OpenAI, Groq, and DeepSeek all expose an (almost) identical ``/chat/completions`` wire format,
so the vendor-specific mapping lives here once; each of the three concrete adapters
(``openai_provider.py``, ``groq_provider.py``, ``deepseek_provider.py``) only sets its own
``default_base_url``, ``pricing_per_1k_tokens``, and provider name.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import AsyncIterator

from app.providers.http_provider_base import HttpJsonProviderBase
from app.providers.schemas import (
    HealthCheckResult,
    ModelInfo,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    TokenUsage,
    ToolCallSchema,
)


class OpenAICompatibleProvider(HttpJsonProviderBase):
    """Base adapter for any vendor implementing the OpenAI Chat Completions API shape."""

    chat_completions_path: str = "/chat/completions"
    models_path: str = "/models"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, request: ProviderRequest) -> list[dict[str, object]]:
        messages: list[dict[str, object]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for message in request.messages:
            entry: dict[str, object] = {"role": message.role, "content": message.content or None}
            if message.name:
                entry["name"] = message.name
            if message.tool_call_id:
                entry["tool_call_id"] = message.tool_call_id
            if message.tool_calls:
                entry["content"] = message.content or None
                entry["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.tool_name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in message.tool_calls
                ]
            messages.append(entry)
        return messages

    def _build_payload(self, request: ProviderRequest) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": request.model,
            "messages": self._build_messages(request),
            "temperature": (
                request.temperature if request.temperature is not None else self.config.temperature
            ),
            "max_tokens": request.max_tokens or self.config.max_tokens,
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in request.tools
            ]
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        return payload

    def _parse_tool_calls(self, message: dict[str, object]) -> list[ToolCallSchema]:
        raw_calls = message.get("tool_calls") or []
        parsed: list[ToolCallSchema] = []
        for call in raw_calls:  # type: ignore[union-attr]
            function = call["function"]
            arguments = function["arguments"]
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"_raw": arguments}
            parsed.append(
                ToolCallSchema(
                    id=call["id"],
                    tool_name=function["name"],
                    arguments=arguments,
                    status="pending",
                    timestamp=dt.datetime.now(dt.UTC),
                )
            )
        return parsed

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send a chat-completions request and return a normalized response."""
        body, latency = await self._request_json(
            "POST",
            self.chat_completions_path,
            json=self._build_payload(request),
            headers=self._headers(),
        )
        choice = body["choices"][0]
        message = choice["message"]
        usage_raw = body.get("usage", {}) or {}
        usage = TokenUsage(
            prompt_tokens=usage_raw.get("prompt_tokens"),
            completion_tokens=usage_raw.get("completion_tokens"),
            total_tokens=usage_raw.get("total_tokens"),
        )
        usage.estimated_cost = await self.estimate_cost(usage, model=request.model)

        return ProviderResponse(
            provider=self.config.provider,
            model=request.model,
            content=message.get("content"),
            reasoning=message.get("reasoning_content"),
            reasoning_available=bool(message.get("reasoning_content")),
            tool_calls=self._parse_tool_calls(message),
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            latency=latency,
            request_id=body.get("id"),
            raw_response=body,
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Streaming is not implemented for the HTTP-only adapters in this build.

        The normalized :class:`~app.providers.schemas.ProviderStreamEvent` contract is defined
        so a future SSE-based implementation is a drop-in replacement (PROJECT_SPEC_2 SS39).
        """
        return super().stream(request)

    async def health_check(self) -> HealthCheckResult:
        """Check reachability via the (free) models-list endpoint rather than a chat call."""
        import time

        start = time.perf_counter()
        try:
            await self._request_json("GET", self.models_path, headers=self._headers())
        except Exception as exc:  # noqa: BLE001 - normalized into the health result
            return HealthCheckResult(provider=self.config.provider, healthy=False, message=str(exc))
        return HealthCheckResult(
            provider=self.config.provider,
            healthy=True,
            latency=time.perf_counter() - start,
        )

    async def list_models(self) -> list[ModelInfo]:
        """List models via the standard OpenAI-compatible ``GET /models`` endpoint."""
        body, _latency = await self._request_json("GET", self.models_path, headers=self._headers())
        return [ModelInfo(name=item["id"]) for item in body.get("data", [])]
