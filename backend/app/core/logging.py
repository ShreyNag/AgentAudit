"""Structured logging configuration.

Every log entry includes a timestamp, level, module, message, and (via
:mod:`app.middleware.correlation`) the current request's correlation ID, per
PROJECT_SPEC_2 SS11. Secrets are never logged (PROJECT_SPEC_2 SS133).
"""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import Processor

from app.middleware.correlation import get_correlation_id

_SENSITIVE_KEYS = frozenset({"api_key", "password", "secret_key", "authorization", "token"})


def _redact_sensitive_values(
    _logger: object, _method_name: str, event_dict: dict[str, object]
) -> dict[str, object]:
    """Redact known-sensitive keys from a structlog event dict before it is emitted."""
    for key in list(event_dict):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict


def _inject_correlation_id(
    _logger: object, _method_name: str, event_dict: dict[str, object]
) -> dict[str, object]:
    """Attach the current request's correlation ID to the log event, if one is set."""
    correlation_id = get_correlation_id()
    if correlation_id is not None:
        event_dict["request_id"] = correlation_id
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog + stdlib logging for the whole process.

    Args:
        log_level: One of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``
            (PROJECT_SPEC_5 SS22).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        _inject_correlation_id,
        _redact_sensitive_values,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[*shared_processors, structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to ``name`` (typically ``__name__``)."""
    return structlog.get_logger(name)
