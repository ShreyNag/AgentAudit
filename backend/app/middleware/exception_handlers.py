"""Centralized exception -> standardized error envelope mapping (PROJECT_SPEC_2 SS12/SS117).

Registered once on the FastAPI application in :func:`app.main.create_app`. No handler ever
returns a raw stack trace to the client; unexpected errors are logged with full context and
returned as a generic ``500`` with a redacted message.
"""

from __future__ import annotations

import datetime as dt

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AgentAuditError
from app.core.logging import get_logger
from app.middleware.correlation import get_correlation_id

logger = get_logger(__name__)


def _error_envelope(
    *, code: str, message: str, details: dict[str, object] | None = None
) -> dict[str, object]:
    """Build the standardized error response body shared by every handler."""
    return {
        "status": "error",
        "code": code,
        "message": message,
        "details": details or {},
        "request_id": get_correlation_id(),
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
    }


async def agentaudit_exception_handler(request: Request, exc: AgentAuditError) -> JSONResponse:
    """Handle any :class:`AgentAuditError` raised while processing a request."""
    logger.warning(
        "agentaudit_error",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_envelope(code=exc.code, message=exc.message, details=exc.details),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI/Pydantic request validation failures with a structured 422 response."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_envelope(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any exception not caught by a more specific handler.

    Logs the full exception server-side but never leaks internals to the client
    (PROJECT_SPEC_2 SS117 / SS24).
    """
    logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_envelope(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        ),
    )
