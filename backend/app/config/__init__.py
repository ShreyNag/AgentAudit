"""Centralized, environment-driven application configuration.

Per PROJECT_SPEC_2 SS8, configuration values must never be read via ``os.getenv()`` outside
this package. Everything else imports :func:`get_settings`.
"""

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
