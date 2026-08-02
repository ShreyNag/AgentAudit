"""Provider-agnostic request/response schemas (PROJECT_SPEC_2 SS36-38, PROJECT_SPEC_6 SS45).

No downstream component may inspect a raw vendor SDK/HTTP response -- everything is normalized
into these Pydantic models before leaving the provider layer.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]


class ToolCallSchema(BaseModel):
    """A normalized tool call, regardless of vendor wire format (PROJECT_SPEC_2 SS38)."""

    id: str
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)
    status: str = "pending"
    timestamp: dt.datetime | None = None


class ProviderMessage(BaseModel):
    """One message in a provider-agnostic conversation.

    ``tool_calls`` carries the structured tool calls an *assistant* turn requested, so a
    provider adapter can round-trip them into whatever vendor-specific representation that
    vendor's API requires a later ``tool`` message's result to reference (e.g. Anthropic's
    ``tool_use``/``tool_result`` pairing, OpenAI's ``tool_calls`` array). Without this, a
    provider has only the assistant's text, and strict APIs reject the follow-up tool result as
    referencing a tool call that was never made.
    """

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCallSchema] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """A provider-agnostic tool definition offered to the model for this request."""

    name: str
    description: str
    parameters: dict[str, object] = Field(default_factory=dict)


class ProviderRequest(BaseModel):
    """A normalized request, translated by each adapter into its vendor's wire format."""

    provider: str
    model: str
    messages: list[ProviderMessage]
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[ToolDefinition] | None = None
    tool_choice: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    """Token accounting for one provider call (PROJECT_SPEC_2 SS42-43).

    ``estimated_cost`` is ``None`` when the provider/model's pricing is unknown, per
    PROJECT_SPEC_2 SS42 ("If unavailable, values should be marked as unknown rather than
    estimated").
    """

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    currency: str = "USD"


class ProviderResponse(BaseModel):
    """A normalized response (PROJECT_SPEC_2 SS37, PROJECT_SPEC_6 SS45)."""

    provider: str
    model: str
    content: str | None = None
    reasoning: str | None = None
    reasoning_available: bool = False
    tool_calls: list[ToolCallSchema] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str | None = None
    latency: float = 0.0
    request_id: str | None = None
    raw_response: dict[str, object] | None = None
    timestamp: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))


class ProviderStreamEvent(BaseModel):
    """One chunk of a streamed response."""

    delta: str = ""
    tool_call_delta: ToolCallSchema | None = None
    finish_reason: str | None = None
    is_final: bool = False


class ModelInfo(BaseModel):
    """Metadata for one model exposed by a provider (PROJECT_SPEC_2 SS45)."""

    name: str
    context_window: int | None = None
    capabilities: list[str] = Field(default_factory=list)
    available: bool = True
    deprecated: bool = False


class HealthCheckResult(BaseModel):
    """The result of a provider health check (PROJECT_SPEC_2 SS44)."""

    provider: str
    healthy: bool
    message: str | None = None
    latency: float | None = None
