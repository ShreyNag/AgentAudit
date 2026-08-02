"""Correlation ID propagation.

Every request is assigned a correlation ID (from the incoming ``X-Request-ID`` header, or a
freshly generated UUID4) that is attached to the response and to every log line emitted while
handling the request, per PROJECT_SPEC_2 SS10/SS11.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import CORRELATION_ID_HEADER

_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Return the correlation ID bound to the current request context, if any."""
    return _correlation_id_var.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assign and propagate a correlation ID for every incoming HTTP request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Bind a correlation ID to the request context and echo it back on the response."""
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        token = _correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            _correlation_id_var.reset(token)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
