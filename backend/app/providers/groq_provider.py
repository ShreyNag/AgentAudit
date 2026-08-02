"""Groq adapter (PROJECT_SPEC_1 SS657-666): Llama, Qwen, Mixtral, Gemma on Groq's LPU inference."""

from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """Adapter for Groq's OpenAI-compatible Chat Completions API."""

    default_base_url = "https://api.groq.com/openai/v1"
    requires_api_key = True
    pricing_per_1k_tokens = {
        "llama-3.3-70b-versatile": (0.00059, 0.00079),
        "mixtral-8x7b-32768": (0.00024, 0.00024),
        "gemma2-9b-it": (0.0002, 0.0002),
    }
