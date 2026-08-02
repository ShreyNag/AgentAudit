"""Anthropic adapter (PROJECT_SPEC_1 SS629-636): Claude Sonnet, Opus, Haiku.

Anthropic's Messages API has a distinct wire format from the OpenAI family: the system prompt
is a top-level field (not a message), tool results are content blocks within a ``user`` message,
and tool calls come back as ``tool_use`` content blocks rather than a ``tool_calls`` array.
"""

from __future__ import annotations

import datetime as dt
import time
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

_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(HttpJsonProviderBase):
    """Adapter for the Anthropic Messages API."""

    default_base_url = "https://api.anthropic.com/v1"
    requires_api_key = True
    pricing_per_1k_tokens = {
        "claude-opus-5": (0.015, 0.075),
        "claude-sonnet-5": (0.003, 0.015),
        "claude-haiku-4-5-20251001": (0.0008, 0.004),
    }

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.config.api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def _build_messages(self, request: ProviderRequest) -> list[dict[str, object]]:
        """Build Anthropic's Messages API turns.

        Two shapes the Chat-Completions-style ``ProviderMessage`` list doesn't map onto
        directly: an assistant turn that made tool calls must carry ``tool_use`` content
        blocks (not just text), and every ``tool_result`` produced in response to one
        multi-tool-call turn must be merged into a single following ``user`` turn -- Anthropic
        rejects consecutive ``user`` turns, which is what one ``tool_result`` per message would
        otherwise produce.
        """
        messages: list[dict[str, object]] = []
        for message in request.messages:
            if message.role == "system":
                continue  # folded into the top-level `system` field instead
            if message.role == "tool":
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": message.tool_call_id,
                    "content": message.content,
                }
                if (
                    messages
                    and messages[-1]["role"] == "user"
                    and messages[-1].get("_tool_results")
                ):
                    messages[-1]["content"].append(tool_result_block)  # type: ignore[union-attr]
                else:
                    messages.append(
                        {"role": "user", "content": [tool_result_block], "_tool_results": True}
                    )
                continue
            if message.role == "assistant" and message.tool_calls:
                content_blocks: list[dict[str, object]] = []
                if message.content:
                    content_blocks.append({"type": "text", "text": message.content})
                content_blocks.extend(
                    {
                        "type": "tool_use",
                        "id": call.id,
                        "name": call.tool_name,
                        "input": call.arguments,
                    }
                    for call in message.tool_calls
                )
                messages.append({"role": "assistant", "content": content_blocks})
                continue
            messages.append({"role": message.role, "content": message.content})
        for entry in messages:
            entry.pop("_tool_results", None)
        return messages

    def _build_payload(self, request: ProviderRequest) -> dict[str, object]:
        system_prompt = request.system_prompt or next(
            (m.content for m in request.messages if m.role == "system"), None
        )
        payload: dict[str, object] = {
            "model": request.model,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "messages": self._build_messages(request),
        }
        if system_prompt:
            payload["system"] = system_prompt
        if request.tools:
            payload["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters or {"type": "object", "properties": {}},
                }
                for tool in request.tools
            ]
        return payload

    def _parse_content_blocks(
        self, blocks: list[dict[str, object]]
    ) -> tuple[str | None, list[ToolCallSchema]]:
        text_parts: list[str] = []
        tool_calls: list[ToolCallSchema] = []
        for block in blocks:
            if block.get("type") == "text":
                text_parts.append(str(block.get("text", "")))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCallSchema(
                        id=str(block["id"]),
                        tool_name=str(block["name"]),
                        arguments=dict(block.get("input", {})),
                        status="pending",
                        timestamp=dt.datetime.now(dt.UTC),
                    )
                )
        content = "\n".join(text_parts) if text_parts else None
        return content, tool_calls

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send a Messages API request and return a normalized response."""
        body, latency = await self._request_json(
            "POST", "/messages", json=self._build_payload(request), headers=self._headers()
        )
        content, tool_calls = self._parse_content_blocks(body.get("content", []))
        usage_raw = body.get("usage", {}) or {}
        usage = TokenUsage(
            prompt_tokens=usage_raw.get("input_tokens"),
            completion_tokens=usage_raw.get("output_tokens"),
            total_tokens=(
                (usage_raw.get("input_tokens") or 0) + (usage_raw.get("output_tokens") or 0)
                if usage_raw
                else None
            ),
        )
        usage.estimated_cost = await self.estimate_cost(usage, model=request.model)

        return ProviderResponse(
            provider=self.config.provider,
            model=request.model,
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=body.get("stop_reason"),
            latency=latency,
            request_id=body.get("id"),
            raw_response=body,
        )

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Streaming is not implemented for the HTTP-only adapter in this build."""
        return super().stream(request)

    async def health_check(self) -> HealthCheckResult:
        """Check reachability via ``GET /models`` rather than a paid Messages call."""
        start = time.perf_counter()
        try:
            await self._request_json("GET", "/models", headers=self._headers())
        except Exception as exc:  # noqa: BLE001 - normalized into the health result
            return HealthCheckResult(provider=self.config.provider, healthy=False, message=str(exc))
        return HealthCheckResult(
            provider=self.config.provider, healthy=True, latency=time.perf_counter() - start
        )

    async def list_models(self) -> list[ModelInfo]:
        """List models via ``GET /models``."""
        body, _latency = await self._request_json("GET", "/models", headers=self._headers())
        return [ModelInfo(name=item["id"]) for item in body.get("data", [])]
