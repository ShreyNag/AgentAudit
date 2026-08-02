"""Unit tests for the AgentAudit exception hierarchy."""

from app.core.exceptions import (
    AgentAuditError,
    BenchmarkEnvironmentError,
    ConfigurationError,
    EvaluationError,
    ExecutionError,
    ExecutionTimeoutError,
    NotFoundError,
    PlannerError,
    ProviderError,
    ToolError,
    TraceError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Every exception must derive from AgentAuditError with the expected code/status."""

    def test_all_top_level_errors_derive_from_base(self) -> None:
        for exc_cls in (
            ConfigurationError,
            ValidationError,
            ProviderError,
            ExecutionError,
            TraceError,
            EvaluationError,
            NotFoundError,
        ):
            assert issubclass(exc_cls, AgentAuditError)

    def test_execution_subtypes_derive_from_execution_error(self) -> None:
        for exc_cls in (ToolError, BenchmarkEnvironmentError, PlannerError, ExecutionTimeoutError):
            assert issubclass(exc_cls, ExecutionError)
            assert issubclass(exc_cls, AgentAuditError)

    def test_message_and_details_are_preserved(self) -> None:
        error = ValidationError("bad input", details={"field": "name"})
        assert error.message == "bad input"
        assert error.details == {"field": "name"}
        assert str(error) == "bad input"

    def test_default_details_is_empty_dict_not_shared(self) -> None:
        first = ValidationError("a")
        second = ValidationError("b")
        first.details["x"] = 1
        assert second.details == {}

    def test_each_error_has_a_unique_code_and_http_status(self) -> None:
        errors = [
            ConfigurationError("x"),
            ValidationError("x"),
            ProviderError("x"),
            ExecutionError("x"),
            ToolError("x"),
            BenchmarkEnvironmentError("x"),
            PlannerError("x"),
            ExecutionTimeoutError("x"),
            TraceError("x"),
            EvaluationError("x"),
            NotFoundError("x"),
        ]
        for error in errors:
            assert isinstance(error.code, str) and error.code
            assert isinstance(error.http_status, int) and 400 <= error.http_status <= 599
