"""OpenAI adapter (PROJECT_SPEC_1 SS619-626): GPT-4.1, GPT-5, GPT-5-mini, GPT-5-nano."""

from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider
from app.providers.schemas import ProviderRequest


class OpenAIProvider(OpenAICompatibleProvider):
    """Adapter for the OpenAI Chat Completions API."""

    default_base_url = "https://api.openai.com/v1"
    requires_api_key = True
    # USD per 1K tokens: (prompt, completion). Illustrative published-tier rates; update as
    # OpenAI's pricing page changes -- estimate_cost() returns None for any model not listed
    # here rather than guessing (PROJECT_SPEC_2 SS42).
    pricing_per_1k_tokens = {
        "gpt-4.1": (0.002, 0.008),
        "gpt-5": (0.005, 0.015),
        "gpt-5-mini": (0.001, 0.004),
        "gpt-5-nano": (0.0002, 0.0008),
    }

    def _build_payload(self, request: ProviderRequest) -> dict[str, object]:
        """Adapt the shared Chat Completions payload to GPT-5/o-series constraints.

        These models reject the classic ``max_tokens`` field ("...Use 'max_completion_tokens'
        instead") and reject any non-default ``temperature`` ("Only the default (1) value is
        supported") -- unlike Groq/DeepSeek, which still speak the older shape this payload
        builder is shared with, so both adjustments are made only here, not in the base class.
        """
        payload = super()._build_payload(request)
        payload["max_completion_tokens"] = payload.pop("max_tokens")
        del payload["temperature"]
        return payload
