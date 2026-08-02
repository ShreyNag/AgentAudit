"""``BaseEnvironment``: the common interface every benchmark environment implements.

Method set is the union of PROJECT_SPEC_2 SS59 and PROJECT_SPEC_6 SS50 -- see
``docs/adr/0004-base-environment-interface.md``. Only tools may call into an environment; the
Agent Under Test never receives direct access (PROJECT_SPEC_1 SS55).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEnvironment(ABC):
    """Abstract base class every concrete benchmark environment must implement."""

    #: Short, unique environment name (e.g. ``"travel"``), matching PROJECT_SPEC_1 SS29.
    name: str

    def __init__(self) -> None:
        """Environments start uninitialized; call :meth:`initialize` before use."""
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Seed the environment with its deterministic starting dataset."""

    @abstractmethod
    async def reset(self) -> None:
        """Restore the environment to its freshly-initialized state (PROJECT_SPEC_1 SS61)."""

    @abstractmethod
    async def observe(self) -> dict[str, Any]:
        """Return the current observable state (a.k.a. ``get_state``)."""

    async def get_state(self) -> dict[str, Any]:
        """Alias for :meth:`observe`, matching PROJECT_SPEC_2 SS59's naming."""
        return await self.observe()

    @abstractmethod
    async def validate_action(self, action: str, parameters: dict[str, Any]) -> bool:
        """Return whether ``action`` with ``parameters`` is well-formed for this environment."""

    @abstractmethod
    async def step(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Apply ``action`` and return the resulting observation (a.k.a. ``apply_action``)."""

    async def apply_action(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Alias for :meth:`step`, matching PROJECT_SPEC_2 SS59's naming."""
        return await self.step(action, parameters)

    @abstractmethod
    async def is_complete(self) -> bool:
        """Return whether this environment considers the current episode finished."""

    @abstractmethod
    async def export_state(self) -> dict[str, Any]:
        """Return a fully serializable snapshot of the environment's current state."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Release any resources held by this environment instance."""
