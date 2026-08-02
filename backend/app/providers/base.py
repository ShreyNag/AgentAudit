"""``BaseProvider``: the common interface every LLM adapter implements.

Method set is the union of PROJECT_SPEC_2 SS30 and PROJECT_SPEC_6 SS43 -- see
``docs/adr/0002-base-provider-interface.md``. ``chat()``, ``reason()``, and ``close()`` have
concrete default implementations here so adapters only need to implement the primitives
(``generate``, ``stream``, ``count_tokens``, ``estimate_cost``, ``health_check``,
``list_models``); adapters that do need bespoke chat/reasoning behavior may still override them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.providers.config import ProviderConfig
from app.providers.schemas import (
    HealthCheckResult,
    ModelInfo,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    TokenUsage,
)


class BaseProvider(ABC):
    """Abstract base class every concrete provider adapter must implement."""

    def __init__(self, config: ProviderConfig) -> None:
        """Store the immutable provider configuration; adapters open connections lazily."""
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Perform any lazy setup required before the first request (e.g. open an HTTP client)."""

    @abstractmethod
    async def validate_configuration(self) -> None:
        """Raise :class:`~app.core.exceptions.ConfigurationError` if required config is missing."""

    @abstractmethod
    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send ``request`` to the underlying LLM and return a normalized response."""

    @abstractmethod
    def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderStreamEvent]:
        """Stream a normalized response as it is generated (a.k.a. ``stream_generate``)."""

    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        """Multi-turn conversational call. Defaults to :meth:`generate`."""
        return await self.generate(request)

    async def reason(self, request: ProviderRequest) -> ProviderResponse:
        """Reasoning-oriented call. Defaults to :meth:`generate`.

        Adapters for providers with a distinct reasoning/thinking mode may override this to
        request it explicitly; otherwise the response's ``reasoning_available`` flag reports
        whether the underlying response actually contained separable reasoning content
        (PROJECT_SPEC_1 SS52/SS63 -- never fabricate reasoning that was not present).
        """
        return await self.generate(request)

    @abstractmethod
    async def count_tokens(self, text: str, *, model: str | None = None) -> int:
        """Return an estimated or exact token count for ``text``."""

    @abstractmethod
    async def estimate_cost(self, usage: TokenUsage, *, model: str | None = None) -> float | None:
        """Return an estimated cost in USD for ``usage``, or ``None`` if pricing is unknown."""

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """Verify authentication and endpoint availability without significant token usage."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return the models available through this provider, if discoverable."""

    async def shutdown(self) -> None:
        """Release any held resources (HTTP clients, etc.). Default is a no-op."""
        return None

    async def close(self) -> None:
        """Alias for :meth:`shutdown`, matching PROJECT_SPEC_2 SS30's naming."""
        await self.shutdown()
