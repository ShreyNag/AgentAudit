"""``ProviderFactory``: resolves a provider name to a configured, initialized adapter instance.

Adding a new provider requires only a new adapter class plus one registry entry here -- nothing
else changes (PROJECT_SPEC_1 SS27/SS1241-1247, PROJECT_SPEC_6 SS44).
"""

from __future__ import annotations

from app.config import Settings
from app.core.exceptions import ConfigurationError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseProvider
from app.providers.config import ProviderConfig
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.sarvam_provider import SarvamProvider

_REGISTRY: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "groq": GroqProvider,
    "ollama": OllamaProvider,
    "sarvam": SarvamProvider,
}


class ProviderFactory:
    """Instantiates and initializes :class:`~app.providers.base.BaseProvider` adapters."""

    @staticmethod
    def register(name: str, provider_cls: type[BaseProvider]) -> None:
        """Register (or replace) the adapter class used for ``name``.

        Exists so tests, plugins, or future providers can extend the registry without editing
        this module (PROJECT_SPEC_1 SS27).
        """
        _REGISTRY[name.lower()] = provider_cls

    @staticmethod
    def supported_providers() -> list[str]:
        """Return every currently registered provider name."""
        return sorted(_REGISTRY)

    @classmethod
    async def create(cls, config: ProviderConfig) -> BaseProvider:
        """Build, initialize, and validate a provider adapter for ``config``.

        Raises:
            ConfigurationError: if ``config.provider`` is not a registered provider name, or if
                the adapter's own configuration validation fails (missing API key/model).
        """
        provider_cls = _REGISTRY.get(config.provider.lower())
        if provider_cls is None:
            raise ConfigurationError(
                f"Unknown provider '{config.provider}'. Supported providers: "
                f"{', '.join(cls.supported_providers())}."
            )
        provider = provider_cls(config)
        await provider.validate_configuration()
        await provider.initialize()
        return provider

    @classmethod
    async def create_aut(cls, settings: Settings) -> BaseProvider:
        """Build the Agent Under Test's provider from the ``AUT_*`` settings group."""
        return await cls.create(
            ProviderConfig(
                provider=settings.aut_provider,
                model=settings.aut_model,
                api_key=settings.aut_api_key,
                base_url=settings.aut_base_url,
                timeout=settings.aut_timeout,
            )
        )

    @classmethod
    async def create_judge(cls, settings: Settings) -> BaseProvider:
        """Build the Judge's provider from the ``JUDGE_*`` settings group.

        Always a separate provider instance from the AUT's, even when both are configured for
        the same vendor, so the two never share connection state (PROJECT_SPEC_2 SS48).
        """
        return await cls.create(
            ProviderConfig(
                provider=settings.judge_provider,
                model=settings.judge_model,
                api_key=settings.judge_api_key,
                base_url=settings.judge_base_url,
                timeout=settings.judge_timeout,
            )
        )
