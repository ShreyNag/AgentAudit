"""``ProviderConfig`` defaults and immutability (PROJECT_SPEC_2 SS33)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.providers.config import ProviderConfig


class TestProviderConfig:
    def test_defaults_apply(self) -> None:
        config = ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="key")
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.base_url is None

    def test_config_is_immutable(self) -> None:
        config = ProviderConfig(provider="anthropic", model="claude-sonnet-5", api_key="key")
        with pytest.raises(ValidationError):
            config.model = "claude-opus-5"  # type: ignore[misc]
