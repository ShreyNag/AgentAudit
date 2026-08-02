"""Google Gemini adapter (PROJECT_SPEC_1 SS639-646): Gemini 2.5 Pro, Flash, Flash Lite.

Gemini's ``generateContent`` API differs from both the OpenAI and Anthropic families: roles are
``user``/``model`` (not ``assistant``), the system prompt is a ``systemInstruction`` object,
tool results are ``functionResponse`` parts on a ``function``-role turn, and authentication is a
query-string API key rather than a header.
"""

from __future__ import annotations

import time
import uuid
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


class GeminiProvider(HttpJsonProviderBase):
    """Adapter for the Google Gemini ``generateContent`` REST API."""

    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    requires_api_key = True
    pricing_per_1k_tokens = {
        "gemini-2.5-pro": (0.00125, 0.005),
        "gemini-2.5-flash": (0.000075, 0.0003),
        "gemini-flash-lite": (0.0000375, 0.00015),
    }

    def _auth_params(self) -> dict[str, str]:
        return {"key": self.config.api_key}

    def _build_contents(self, request: ProviderRequest) -> list[dict[str, object]]:
        """Build Gemini's ``contents`` turns.

        Two shapes the Chat-Completions-style ``ProviderMessage`` list doesn't map onto
        directly: a ``model`` turn that made tool calls must carry ``functionCall`` parts (not
        just text), so a later ``functionResponse`` part references a call Gemini actually
        sees as having been made; and every ``functionResponse`` produced in response to one
        multi-tool-call turn is merged into a single following ``function`` turn rather than one
        turn per call.
        """
        contents: list[dict[str, object]] = []
        for message in request.messages:
            if message.role == "system":
                continue  # folded into systemInstruction instead
            if message.role == "tool":
                function_response_part = {
                    "functionResponse": {
                        "name": message.name or "tool",
                        "response": {"content": message.content},
                    }
                }
                if contents and contents[-1]["role"] == "function":
                    contents[-1]["parts"].append(function_response_part)  # type: ignore[union-attr]
                else:
                    contents.append({"role": "function", "parts": [function_response_part]})
                continue
            if message.role == "assistant" and message.tool_calls:
                parts: list[dict[str, object]] = []
                if message.content:
                    parts.append({"text": message.content})
                parts.extend(
                    {"functionCall": {"name": call.tool_name, "args": call.arguments}}
                    for call in message.tool_calls
                )
                contents.append({"role": "model", "parts": parts})
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        return contents

    def _build_payload(self, request: ProviderRequest) -> dict[str, object]:
        system_prompt = request.system_prompt or next(
            (m.content for m in request.messages if m.role == "system"), None
        )
        payload: dict[str, object] = {
            "contents": self._build_contents(request),
            "generationConfig": {
                "temperature": (
                    request.temperature
                    if request.temperature is not None
                    else self.config.temperature
                ),
                "maxOutputTokens": request.max_tokens or self.config.max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if request.tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters or {"type": "object", "properties": {}},
                        }
                        for tool in request.tools
                    ]
                }
            ]
        return payload

    def _parse_parts(
        self, parts: list[dict[str, object]]
    ) -> tuple[str | None, list[ToolCallSchema]]:
        text_parts: list[str] = []
        tool_calls: list[ToolCallSchema] = []
        for part in parts:
            if "text" in part:
                text_parts.append(str(part["text"]))
            elif "functionCall" in part:
                call = part["functionCall"]
                tool_calls.append(
                    ToolCallSchema(
                        id=str(uuid.uuid4()),
                        tool_name=str(call["name"]),
                        arguments=dict(call.get("args", {})),
                        status="pending",
                    )
                )
        content = "\n".join(text_parts) if text_parts else None
        return content, tool_calls

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send a ``generateContent`` request and return a normalized response."""
        body, latency = await self._request_json(
            "POST",
            f"/models/{request.model}:generateContent",
            json=self._build_payload(request),
            params=self._auth_params(),
        )
        candidate = body["candidates"][0]
        content, tool_calls = self._parse_parts(candidate.get("content", {}).get("parts", []))
        usage_raw = body.get("usageMetadata", {}) or {}
        usage = TokenUsage(
            prompt_tokens=usage_raw.get("promptTokenCount"),
            completion_tokens=usage_raw.get("candidatesTokenCount"),
            total_tokens=usage_raw.get("totalTokenCount"),
        )
        usage.estimated_cost = await self.estimate_cost(usage, model=request.model)

        return ProviderResponse(
            provider=self.config.provider,
            model=request.model,
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=candidate.get("finishReason"),
            latency=latency,
            raw_response=body,
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Streaming is not implemented for the HTTP-only adapter in this build."""
        return super().stream(request)

    async def health_check(self) -> HealthCheckResult:
        """Check reachability via the free models-list endpoint."""
        start = time.perf_counter()
        try:
            await self._request_json("GET", "/models", params=self._auth_params())
        except Exception as exc:  # noqa: BLE001 - normalized into the health result
            return HealthCheckResult(provider=self.config.provider, healthy=False, message=str(exc))
        return HealthCheckResult(
            provider=self.config.provider, healthy=True, latency=time.perf_counter() - start
        )

    async def list_models(self) -> list[ModelInfo]:
        """List models via ``GET /models``."""
        body, _latency = await self._request_json("GET", "/models", params=self._auth_params())
        return [
            ModelInfo(name=str(item["name"]).rsplit("/", maxsplit=1)[-1])
            for item in body.get("models", [])
        ]
