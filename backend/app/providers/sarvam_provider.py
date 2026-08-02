"""Sarvam AI adapter: Indian-language-focused chat models (``sarvam-105b``, ``sarvam-30b``)."""

from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider


class SarvamProvider(OpenAICompatibleProvider):
    """Adapter for Sarvam AI's OpenAI-compatible Chat Completions API."""

    default_base_url = "https://api.sarvam.ai/v1"
    requires_api_key = True
    pricing_per_1k_tokens: dict[str, tuple[float, float]] = {}
