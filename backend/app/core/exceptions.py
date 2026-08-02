"""AgentAudit exception hierarchy.

Per PROJECT_SPEC_6 SS28, all application errors derive from :class:`AgentAuditError` so that
application code never depends on provider- or library-specific exception types
(PROJECT_SPEC_2 SS47). Every exception carries a machine-readable ``code`` used to build the
standardized API error envelope (PROJECT_SPEC_2 SS117) and an HTTP status hint used by the
FastAPI exception handlers in :mod:`app.middleware.exception_handlers`.
"""

from __future__ import annotations


class AgentAuditError(Exception):
    """Base class for every AgentAudit-specific exception.

    Attributes:
        code: Machine-readable error code, e.g. ``"VALIDATION_ERROR"``.
        details: Optional structured context safe to return to API clients.
        http_status: Default HTTP status code used when this error escapes to the API layer.
    """

    code: str = "AGENTAUDIT_ERROR"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        """Initialize the error with a human-readable message and optional structured details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(AgentAuditError):
    """Raised when required configuration is missing or invalid at startup or runtime."""

    code = "CONFIGURATION_ERROR"
    http_status = 500


class ValidationError(AgentAuditError):
    """Raised when external input (API request, tool arguments, benchmark definition) is invalid."""

    code = "VALIDATION_ERROR"
    http_status = 400


class ProviderError(AgentAuditError):
    """Base class for all LLM provider communication errors (PROJECT_SPEC_2 SS47)."""

    code = "PROVIDER_ERROR"
    http_status = 502


class ExecutionError(AgentAuditError):
    """Base class for errors raised while executing an Agent Under Test."""

    code = "EXECUTION_ERROR"
    http_status = 500


class ToolError(ExecutionError):
    """Raised when a tool invocation fails in a way that is not recoverable."""

    code = "TOOL_ERROR"
    http_status = 500


class BenchmarkEnvironmentError(ExecutionError):
    """Raised when a benchmark environment cannot initialize, reset, or apply an action."""

    code = "ENVIRONMENT_ERROR"
    http_status = 500


class PlannerError(ExecutionError):
    """Raised when the execution planner cannot determine a valid next action."""

    code = "PLANNER_ERROR"
    http_status = 500


class ExecutionTimeoutError(ExecutionError):
    """Raised when execution exceeds its configured timeout or iteration/tool-call limits."""

    code = "EXECUTION_TIMEOUT"
    http_status = 504


class TraceError(AgentAuditError):
    """Raised on trace construction, serialization, persistence, or replay failures."""

    code = "TRACE_ERROR"
    http_status = 500


class EvaluationError(AgentAuditError):
    """Raised when the Evaluation Engine cannot complete evaluation of a persisted trace."""

    code = "EVALUATION_ERROR"
    http_status = 500


class NotFoundError(AgentAuditError):
    """Raised when a requested resource (run, trace, benchmark, provider) does not exist."""

    code = "NOT_FOUND"
    http_status = 404
