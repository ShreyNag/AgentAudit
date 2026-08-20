"""Ollama adapter (PROJECT_SPEC_1 SS669-672): any locally installed model, no API key or cost."""

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


class OllamaProvider(HttpJsonProviderBase):
    """Adapter for a local Ollama server's ``/api/chat`` endpoint."""

    default_base_url = "http://localhost:11434"
    requires_api_key = False
    # Local inference has no per-token cost; estimate_cost() always returns None.
    pricing_per_1k_tokens = {}

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _build_messages(self, request: ProviderRequest) -> list[dict[str, object]]:
        messages: list[dict[str, object]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for message in request.messages:
            messages.append({"role": message.role, "content": message.content})
        return messages

    def _build_payload(self, request: ProviderRequest) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": request.model,
            "messages": self._build_messages(request),
            "stream": False,
            "options": {
                "temperature": (
                    request.temperature
                    if request.temperature is not None
                    else self.config.temperature
                ),
                "num_predict": request.max_tokens or self.config.max_tokens,
            },
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
        # Ollama's own grammar-constrained decoding is far more reliable than prompt-only
        # instructions at getting a small local model (e.g. the Judge's rubric-JSON output) to
        # actually emit valid JSON -- smaller models frequently add prose or truncate otherwise.
        # Only applied when explicitly requested (app.evaluation.judge.JudgeService.submit sets
        # this) and never alongside tool-calling, where content isn't meant to be pure JSON.
        if request.metadata.get("response_format") == "json" and not request.tools:
            payload["format"] = "json"
        return payload

    def _parse_tool_calls(self, message: dict[str, object]) -> list[ToolCallSchema]:
        raw_calls = message.get("tool_calls") or []
        parsed: list[ToolCallSchema] = []
        for call in raw_calls:  # type: ignore[union-attr]
            function = call.get("function", {})
            parsed.append(
                ToolCallSchema(
                    id=str(call.get("id") or uuid.uuid4()),
                    tool_name=str(function.get("name")),
                    arguments=dict(function.get("arguments", {})),
                    status="pending",
                )
            )
        return parsed

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send a chat request to the local Ollama server and return a normalized response."""
        body, latency = await self._request_json(
            "POST", "/api/chat", json=self._build_payload(request), headers=self._headers()
        )
        message = body.get("message", {})
        prompt_tokens = body.get("prompt_eval_count")
        completion_tokens = body.get("eval_count")
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=(
                (prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None or completion_tokens is not None
                else None
            ),
            estimated_cost=None,
        )

        return ProviderResponse(
            provider=self.config.provider,
            model=request.model,
            content=message.get("content"),
            tool_calls=self._parse_tool_calls(message),
            usage=usage,
            finish_reason=body.get("done_reason") or ("stop" if body.get("done") else None),
            latency=latency,
            raw_response=body,
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Streaming is not implemented for the HTTP-only adapter in this build."""
        return super().stream(request)

    async def health_check(self) -> HealthCheckResult:
        """Check both that the local Ollama server is reachable AND that ``self.config.model``
        is actually pulled -- a reachable-but-model-missing Ollama server is not usable, and
        would otherwise only fail later, mid-evaluation, with a much less specific error.

        Ollama treats a tag-less name (e.g. ``"llama3.1"``) as implicitly ``:latest``
        (``"llama3.1:latest"``), and ``GET /api/tags`` always returns the fully-tagged name --
        so the configured model is checked against both forms rather than a naive exact match,
        which would otherwise wrongly report a tag-less name as unavailable.
        """
        start = time.perf_counter()
        try:
            body, _latency = await self._request_json("GET", "/api/tags", headers=self._headers())
        except Exception as exc:  # noqa: BLE001 - normalized into the health result
            return HealthCheckResult(provider=self.config.provider, healthy=False, message=str(exc))

        available = {str(item["name"]) for item in body.get("models", [])}  # type: ignore[attr-defined]
        wanted = self.config.model
        wanted_with_tag = wanted if ":" in wanted else f"{wanted}:latest"
        if wanted not in available and wanted_with_tag not in available:
            return HealthCheckResult(
                provider=self.config.provider,
                healthy=False,
                message=(
                    f"Ollama is reachable, but model '{wanted}' is not pulled. Available: "
                    f"{', '.join(sorted(available)) or '(none)'}. Run: ollama pull {wanted}"
                ),
            )
        return HealthCheckResult(
            provider=self.config.provider, healthy=True, latency=time.perf_counter() - start
        )

    async def list_models(self) -> list[ModelInfo]:
        """List locally pulled models via ``GET /api/tags``."""
        body, _latency = await self._request_json("GET", "/api/tags", headers=self._headers())
        return [ModelInfo(name=item["name"]) for item in body.get("models", [])]
