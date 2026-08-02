"""``ProviderFactory`` registry, construction, and AUT/Judge independence.

PROJECT_SPEC_2 SS31-32/48.
"""

from __future__ import annotations

import pytest

from app.config.settings import Settings
from app.core.exceptions import ConfigurationError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.config import ProviderConfig
from app.providers.factory import ProviderFactory
from app.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
class TestProviderFactory:
    async def test_unknown_provider_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError):
            await ProviderFactory.create(
                ProviderConfig(provider="not-a-real-provider", model="x", api_key="x")
            )

    async def test_create_builds_the_registered_adapter_type(self) -> None:
        provider = await ProviderFactory.create(
            ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="test-key")
        )
        try:
            assert isinstance(provider, AnthropicProvider)
        finally:
            await provider.shutdown()

    async def test_missing_api_key_raises_configuration_error_for_key_requiring_providers(
        self,
    ) -> None:
        with pytest.raises(ConfigurationError):
            await ProviderFactory.create(
                ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="")
            )

    async def test_ollama_does_not_require_an_api_key(self) -> None:
        provider = await ProviderFactory.create(
            ProviderConfig(provider="ollama", model="llama3", api_key="")
        )
        try:
            assert isinstance(provider, OllamaProvider)
        finally:
            await provider.shutdown()

    async def test_aut_and_judge_are_independent_provider_instances(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AUT_PROVIDER", "anthropic")
        monkeypatch.setenv("AUT_MODEL", "claude-sonnet-5")
        monkeypatch.setenv("AUT_API_KEY", "aut-key")
        monkeypatch.setenv("JUDGE_PROVIDER", "openai")
        monkeypatch.setenv("JUDGE_MODEL", "gpt-5")
        monkeypatch.setenv("JUDGE_API_KEY", "judge-key")
        settings = Settings(_env_file=None)

        aut = await ProviderFactory.create_aut(settings)
        judge = await ProviderFactory.create_judge(settings)
        try:
            assert aut is not judge
            assert aut.config.provider == "anthropic"
            assert judge.config.provider == "openai"
        finally:
            await aut.shutdown()
            await judge.shutdown()

    def test_register_extends_the_registry_without_editing_this_module(self) -> None:
        ProviderFactory.register("anthropic-alias-for-test", AnthropicProvider)
        assert "anthropic-alias-for-test" in ProviderFactory.supported_providers()
