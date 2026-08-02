"""``BaseTool``: the common interface every tool implements.

Method set is the union of PROJECT_SPEC_1/2 SS30/SS64 and PROJECT_SPEC_6 SS47 -- see
``docs/adr/0003-base-tool-interface.md``. :class:`EnvironmentActionTool` is a convenience base
that most concrete tools use: it validates arguments against the tool's own JSON-Schema-like
``parameters()`` and dispatches execution to the owning environment's ``step()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.environments.base import BaseEnvironment
from app.tools.validation import validate_arguments_against_schema


class BaseTool(ABC):
    """Abstract base class every concrete tool must implement."""

    #: Unique tool name, e.g. ``"flight_search"`` (matches the owning environment's action name).
    name: str
    #: Human-readable description, shown to the AUT when constructing tool calls.
    description: str
    #: The benchmark environment this tool is scoped to, e.g. ``"travel"``.
    environment_name: str
    #: Semantic version of this tool's contract.
    version: str = "1.0"

    def __init__(self, environment: BaseEnvironment) -> None:
        """Bind this tool instance to the environment it will operate against."""
        self.environment = environment

    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Return this tool's input arguments as a JSON-Schema-like ``dict``."""

    def schema(self) -> dict[str, Any]:
        """Alias for :meth:`parameters`, matching PROJECT_SPEC_1/2's naming."""
        return self.parameters()

    def metadata(self) -> dict[str, Any]:
        """Return the full tool metadata contract (PROJECT_SPEC_1 SS65)."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "environment": self.environment_name,
            "input_schema": self.parameters(),
        }

    @abstractmethod
    async def validate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate (and optionally normalize) raw arguments before execution."""

    async def validate_input(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Alias for :meth:`validate`, matching PROJECT_SPEC_1/2's naming."""
        return await self.validate(arguments)

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool against its bound environment and return the raw result."""

    def serialize_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Serialize ``result`` for trace logging. Default is a pass-through."""
        return result

    async def reset(self) -> None:
        """Reset any tool-local state. Tools are stateless by default (PROJECT_SPEC_2 SS64)."""
        return None

    async def health_check(self) -> bool:
        """Return whether this tool is currently usable. Default is always healthy."""
        return True


class EnvironmentActionTool(BaseTool):
    """Convenience base for tools that map 1:1 onto one environment ``step()`` action."""

    #: The environment-level action name this tool dispatches to via ``environment.step()``.
    action_name: str

    async def validate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate ``arguments`` against :meth:`parameters` (PROJECT_SPEC_2 SS68)."""
        return validate_arguments_against_schema(self.parameters(), arguments, tool_name=self.name)

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the bound environment's ``step()`` for :attr:`action_name`."""
        return await self.environment.step(self.action_name, arguments)
