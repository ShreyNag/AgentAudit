"""Shared HTTP plumbing for JSON-over-HTTPS provider adapters.

Every concrete adapter (OpenAI-compatible, Anthropic, Gemini, Ollama) needs the same
boilerplate: an ``httpx.AsyncClient`` lifecycle, exponential-backoff retry on transient
failures, and HTTP-status -> typed-exception normalization (PROJECT_SPEC_2 SS40-41/SS47). That
boilerplate lives here so each concrete adapter only implements vendor-specific request/response
mapping, while still being a fully independent :class:`~app.providers.base.BaseProvider`
subclass that could be registered in the factory on its own.
"""

from __future__ import annotations

import datetime as dt
import time
from collections.abc import AsyncIterator

import httpx
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import ConfigurationError
from app.providers.base import BaseProvider
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from app.providers.schemas import ProviderRequest, ProviderStreamEvent, TokenUsage

_RETRIABLE_EXCEPTIONS = (ProviderRateLimitError, ProviderTimeoutError, ProviderConnectionError)

_EXPONENTIAL_WAIT = wait_exponential(multiplier=1, min=1, max=30)
#: Cap on how long we'll honor a vendor's Retry-After hint for -- past this it's cheaper to give
#: up and let the batch script record a per-task error than to block the whole run waiting.
_MAX_RETRY_AFTER_WAIT = 60.0


def _wait_for_retry(retry_state: RetryCallState) -> float:
    """Wait the vendor's requested ``Retry-After`` duration on a 429, else exponential backoff.

    Free-tier rate limits (e.g. Groq's per-minute token budget) publish exactly how long until
    the window resets; blind exponential backoff either wastes time overshooting or, worse, keeps
    retrying too fast and exhausts the retry budget before the window actually clears.
    """
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        return min(float(retry_after) + 0.5, _MAX_RETRY_AFTER_WAIT)
    return _EXPONENTIAL_WAIT(retry_state)


class HttpJsonProviderBase(BaseProvider):
    """Base class for adapters that speak JSON-over-HTTPS to a vendor's REST API."""

    #: Default API base URL, overridable via ``ProviderConfig.base_url``.
    default_base_url: str = ""
    #: Whether this provider requires a non-empty API key (false for local providers like Ollama).
    requires_api_key: bool = True
    #: ``{model_name: (prompt_usd_per_1k, completion_usd_per_1k)}``; empty means "unknown" for
    #: every model, so :meth:`estimate_cost` returns ``None`` rather than a guess.
    pricing_per_1k_tokens: dict[str, tuple[float, float]] = {}

    def __init__(self, config: object) -> None:
        """Initialize with an unset HTTP client; the client opens lazily in :meth:`initialize`."""
        super().__init__(config)  # type: ignore[arg-type]
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        """Return the effective API base URL (config override, else the adapter's default)."""
        return self.config.base_url or self.default_base_url

    async def initialize(self) -> None:
        """Open the shared ``httpx.AsyncClient`` used for every subsequent request."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.config.timeout)

    async def validate_configuration(self) -> None:
        """Verify a model is configured, and an API key is present when required."""
        if self.requires_api_key and not self.config.api_key:
            raise ConfigurationError(f"{self.config.provider} requires AUT_API_KEY/JUDGE_API_KEY.")
        if not self.config.model:
            raise ConfigurationError(f"{self.config.provider} requires a model to be configured.")

    async def shutdown(self) -> None:
        """Close the shared HTTP client, if one was opened."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Default streaming implementation: not supported unless an adapter overrides it."""

        async def _unsupported() -> AsyncIterator[ProviderStreamEvent]:
            raise ProviderUnavailableError(
                f"{self.config.provider} does not implement streaming in this adapter."
            )
            yield  # pragma: no cover - makes this an async generator

        return _unsupported()

    async def count_tokens(self, text: str, *, model: str | None = None) -> int:
        """Approximate token count (~4 characters/token) when no exact tokenizer is wired up.

        This is intentionally an estimate, not an exact count, consistent with
        PROJECT_SPEC_2 SS42 allowing either.
        """
        return max(1, len(text) // 4)

    async def estimate_cost(self, usage: TokenUsage, *, model: str | None = None) -> float | None:
        """Estimate cost from :attr:`pricing_per_1k_tokens`, or ``None`` if the model is unknown."""
        rates = self.pricing_per_1k_tokens.get(model or self.config.model)
        if rates is None or usage.prompt_tokens is None or usage.completion_tokens is None:
            return None
        prompt_rate, completion_rate = rates
        return round(
            (usage.prompt_tokens / 1000) * prompt_rate
            + (usage.completion_tokens / 1000) * completion_rate,
            6,
        )

    def _client_or_raise(self) -> httpx.AsyncClient:
        """Return the initialized HTTP client, or raise if :meth:`initialize` was never called."""
        if self._client is None:
            raise ConfigurationError(
                f"{self.config.provider} adapter was not initialized before use."
            )
        return self._client

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        """Parse the ``Retry-After`` header (seconds, or an HTTP-date) if the vendor sent one."""
        header = response.headers.get("retry-after")
        if not header:
            return None
        try:
            return max(0.0, float(header))
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime

                target = parsedate_to_datetime(header)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=dt.UTC)
                return max(0.0, (target - dt.datetime.now(dt.UTC)).total_seconds())
            except (TypeError, ValueError):
                return None

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Translate an HTTP error status into the matching typed provider exception."""
        if response.status_code < 400:
            return
        message = (
            f"{self.config.provider} returned HTTP {response.status_code}: {response.text[:500]}"
        )
        if response.status_code in (401, 403):
            raise ProviderAuthenticationError(message)
        if response.status_code == 429:
            raise ProviderRateLimitError(message, retry_after=self._retry_after_seconds(response))
        if response.status_code in (408, 504):
            raise ProviderTimeoutError(message)
        if response.status_code in (400, 422):
            raise ProviderValidationError(message)
        raise ProviderUnavailableError(message)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> tuple[dict[str, object], float]:
        """Issue an HTTP request with retry/backoff, returning ``(response_json, latency_seconds)``.

        Retries only transient failures (rate limits, timeouts, connection errors) with
        exponential backoff, up to ``config.max_retries`` attempts (PROJECT_SPEC_2 SS40).
        """
        client = self._client_or_raise()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max(1, self.config.max_retries)),
            wait=_wait_for_retry,
            retry=retry_if_exception_type(_RETRIABLE_EXCEPTIONS),
            reraise=True,
        ):
            with attempt:
                start = time.perf_counter()
                try:
                    response = await client.request(
                        method, path, json=json, headers=headers, params=params
                    )
                except httpx.TimeoutException as exc:
                    raise ProviderTimeoutError(
                        f"{self.config.provider} request timed out."
                    ) from exc
                except httpx.ConnectError as exc:
                    raise ProviderConnectionError(
                        f"Could not connect to {self.config.provider}."
                    ) from exc
                self._raise_for_status(response)
                latency = time.perf_counter() - start
                return response.json(), latency

        # Unreachable: AsyncRetrying with reraise=True always raises or returns above.
        raise ProviderUnavailableError(f"{self.config.provider} request failed after retries.")
