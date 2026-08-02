"""DeepSeek adapter (PROJECT_SPEC_1 SS649-655): DeepSeek Chat, DeepSeek Reasoner."""

from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    """Adapter for DeepSeek's OpenAI-compatible Chat Completions API.

    ``deepseek-reasoner`` returns chain-of-thought in a ``reasoning_content`` message field,
    which :meth:`OpenAICompatibleProvider.generate` already surfaces via
    ``ProviderResponse.reasoning`` / ``reasoning_available``.
    """

    default_base_url = "https://api.deepseek.com"
    requires_api_key = True
    pricing_per_1k_tokens = {
        "deepseek-chat": (0.00027, 0.0011),
        "deepseek-reasoner": (0.00055, 0.00219),
    }
