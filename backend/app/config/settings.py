"""Application configuration.

Implements the generic, provider-agnostic ``.env`` contract defined in PROJECT_SPEC_1 SS15/SS100
and PROJECT_SPEC_2 SS7-SS8: every setting is read once at startup from environment variables /
``.env``, with typed defaults, and grouped by concern (AUT, Judge, Database, Application,
Evaluation, Logging). Changing the AUT or Judge provider must require only editing these
values -- never a code change (PROJECT_SPEC_1 SS15).
"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchored to this file's location (backend/app/config/settings.py -> backend/.env) rather than a
# path relative to the process's current working directory. A cwd-relative env_file (the
# pydantic-settings default pattern) silently finds the wrong file -- or no file at all, falling
# back to field defaults with no warning -- whenever uvicorn is launched from a directory other
# than exactly "backend/", which depends entirely on how the user's shell/IDE starts the server.
_BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Strongly typed, environment-driven settings for the entire backend.

    Fields are grouped by comment section to mirror PROJECT_SPEC_1 SS100's generic ``.env``
    layout. Values are read once at process startup (PROJECT_SPEC_2 SS7) and are treated as
    immutable thereafter.
    """

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # --- AUT (Agent Under Test) ---
    aut_provider: str = Field(default="anthropic", alias="AUT_PROVIDER")
    aut_model: str = Field(default="", alias="AUT_MODEL")
    aut_api_key: str = Field(default="", alias="AUT_API_KEY")
    aut_base_url: str | None = Field(default=None, alias="AUT_BASE_URL")
    # Local providers (e.g. Ollama) can be far slower per call than a hosted API -- cold model
    # loads and CPU inference routinely exceed the 60s default, so this is raisable per-.env
    # without a code change (PROJECT_SPEC_1 SS15).
    aut_timeout: float = Field(default=60.0, alias="AUT_TIMEOUT")

    # --- Judge ---
    judge_provider: str = Field(default="openai", alias="JUDGE_PROVIDER")
    judge_model: str = Field(default="", alias="JUDGE_MODEL")
    judge_api_key: str = Field(default="", alias="JUDGE_API_KEY")
    judge_base_url: str | None = Field(default=None, alias="JUDGE_BASE_URL")
    judge_timeout: float = Field(default=60.0, alias="JUDGE_TIMEOUT")

    # --- MySQL ---
    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="agentaudit", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="password", alias="MYSQL_PASSWORD")
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    # --- Application ---
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # --- Evaluation ---
    enable_behaviour_classification: bool = Field(
        default=True, alias="ENABLE_BEHAVIOUR_CLASSIFICATION"
    )
    enable_failure_attribution: bool = Field(default=True, alias="ENABLE_FAILURE_ATTRIBUTION")
    enable_confidence_scoring: bool = Field(default=True, alias="ENABLE_CONFIDENCE_SCORING")
    enable_reasoning_storage: bool = Field(default=True, alias="ENABLE_REASONING_STORAGE")
    enable_execution_trace: bool = Field(default=True, alias="ENABLE_EXECUTION_TRACE")

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Versioning (PROJECT_SPEC_1 SS111) ---
    application_version: str = "0.1.0"
    framework_version: str = "0.1.0"
    execution_trace_version: str = "1.0"
    benchmark_version: str = "1.0"

    @property
    def database_url(self) -> str:
        """Return the async SQLAlchemy DSN.

        Uses ``DATABASE_URL`` verbatim when set (local/dev/CI override, e.g. SQLite); otherwise
        builds a MySQL 8+ DSN from the individual ``MYSQL_*`` fields, since MySQL is the primary
        persistence layer (PROJECT_SPEC_1 SS74).
        """
        if self.database_url_override:
            return self.database_url_override
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+aiomysql://{user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def is_sqlite(self) -> bool:
        """Return whether the active database DSN targets SQLite."""
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` singleton.

    Cached with :func:`functools.lru_cache` so configuration is parsed exactly once per
    process, per PROJECT_SPEC_2 SS7 ("Configuration is read once during startup").
    """
    return Settings()
