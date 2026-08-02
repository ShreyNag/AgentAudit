"""Unit tests for environment-driven Settings parsing (PROJECT_SPEC_1 SS100)."""

import pytest

from app.config.settings import Settings


class TestSettingsDefaults:
    """Sensible defaults apply when environment variables are unset."""

    def test_defaults_are_populated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUT_PROVIDER", raising=False)
        settings = Settings(_env_file=None)
        assert settings.aut_provider == "anthropic"
        assert settings.judge_provider == "openai"
        assert settings.mysql_port == 3306
        assert settings.enable_behaviour_classification is True


class TestSettingsFromEnvironment:
    """Every documented .env variable is read without requiring code changes."""

    def test_aut_and_judge_are_independently_configurable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AUT_PROVIDER", "gemini")
        monkeypatch.setenv("AUT_MODEL", "gemini-2.5-pro")
        monkeypatch.setenv("JUDGE_PROVIDER", "anthropic")
        monkeypatch.setenv("JUDGE_MODEL", "claude-opus-5")
        settings = Settings(_env_file=None)
        assert settings.aut_provider == "gemini"
        assert settings.aut_model == "gemini-2.5-pro"
        assert settings.judge_provider == "anthropic"
        assert settings.judge_model == "claude-opus-5"

    def test_database_url_override_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./x.db")
        settings = Settings(_env_file=None)
        assert settings.database_url == "sqlite+aiosqlite:///./x.db"
        assert settings.is_sqlite is True

    def test_mysql_dsn_is_built_from_components_when_no_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("MYSQL_HOST", "db.internal")
        monkeypatch.setenv("MYSQL_PORT", "3307")
        monkeypatch.setenv("MYSQL_DATABASE", "agentaudit_test")
        monkeypatch.setenv("MYSQL_USER", "aa")
        monkeypatch.setenv("MYSQL_PASSWORD", "secret")
        settings = Settings(_env_file=None)
        assert (
            settings.database_url == "mysql+aiomysql://aa:secret@db.internal:3307/agentaudit_test"
        )
        assert settings.is_sqlite is False

    def test_settings_is_cached_as_a_singleton(self) -> None:
        from app.config.settings import get_settings

        get_settings.cache_clear()
        first = get_settings()
        second = get_settings()
        assert first is second
        get_settings.cache_clear()
