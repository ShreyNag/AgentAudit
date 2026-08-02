"""Provider-specific exception hierarchy (PROJECT_SPEC_2 SS47).

Every concrete adapter must raise only these types (never a raw ``httpx`` exception or vendor
SDK exception) so that application code never depends on provider internals.
"""

from __future__ import annotations

from app.core.exceptions import ProviderError


class ProviderAuthenticationError(ProviderError):
    """Raised on 401/403 responses -- invalid or missing API key."""

    code = "PROVIDER_AUTHENTICATION_ERROR"
    http_status = 502


class ProviderRateLimitError(ProviderError):
    """Raised on 429 responses. Eligible for retry with backoff (PROJECT_SPEC_2 SS40/SS118)."""

    code = "PROVIDER_RATE_LIMIT"
    http_status = 429

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        """``retry_after``: seconds the vendor's ``Retry-After`` header asked us to wait, if any."""
        super().__init__(message)
        self.retry_after = retry_after


class ProviderTimeoutError(ProviderError):
    """Raised when a request exceeds its configured timeout. Eligible for retry."""

    code = "PROVIDER_TIMEOUT"
    http_status = 504


class ProviderConnectionError(ProviderError):
    """Raised on network-level connection failures. Eligible for retry."""

    code = "PROVIDER_CONNECTION_ERROR"
    http_status = 502


class ProviderValidationError(ProviderError):
    """Raised on 400/422 responses -- the request itself was malformed. Not retried."""

    code = "PROVIDER_VALIDATION_ERROR"
    http_status = 400


class ProviderUnavailableError(ProviderError):
    """Raised on 500/503 responses or when a provider/model is not configured."""

    code = "PROVIDER_UNAVAILABLE"
    http_status = 503
