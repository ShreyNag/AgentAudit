"""``ToolRegistry`` (PROJECT_SPEC_1 SS31, PROJECT_SPEC_6 SS46).

The runner never imports tools directly -- it queries this registry, so new tools register
without any runner change (PROJECT_SPEC_1 SS31/SS107).
"""

from __future__ import annotations

import time
from collections.abc import Callable

from app.core.exceptions import BenchmarkEnvironmentError, NotFoundError, ToolError
from app.environments.base import BaseEnvironment
from app.tools.base import BaseTool
from app.tools.schemas import ToolInvocationResult

#: Failure types considered "recoverable" at the tool-invocation boundary: they are captured
#: onto the ToolInvocationResult rather than propagated, so one bad tool call never aborts the
#: whole run (PROJECT_SPEC_2 SS53/SS110, PROJECT_SPEC_6 SS48). A malformed call (ToolError) and
#: an environment-level rejection (e.g. insufficient balance/inventory) are both recoverable in
#: exactly this sense.
_RECOVERABLE_TOOL_FAILURES = (ToolError, BenchmarkEnvironmentError)

ToolFactory = Callable[[BaseEnvironment], BaseTool]


class ToolRegistry:
    """Registry of tool factories, keyed by tool name."""

    def __init__(self) -> None:
        """Start with an empty registry; concrete tools register at import time."""
        self._factories: dict[str, ToolFactory] = {}

    def register(self, name: str, factory: ToolFactory) -> None:
        """Register (or replace) the factory used to construct tool ``name``.

        Raises:
            ToolError: if ``name`` is already registered to a different factory, guarding
                against accidental duplicate tool names across environments.
        """
        existing = self._factories.get(name)
        if existing is not None and existing is not factory:
            raise ToolError(f"Tool name '{name}' is already registered to a different factory.")
        self._factories[name] = factory

    def is_registered(self, name: str) -> bool:
        """Return whether ``name`` has a registered factory."""
        return name in self._factories

    def list_tools(self) -> list[str]:
        """Return every registered tool name."""
        return sorted(self._factories)

    def create(self, name: str, environment: BaseEnvironment) -> BaseTool:
        """Construct a tool instance bound to ``environment``.

        Raises:
            NotFoundError: if no tool is registered under ``name``.
        """
        factory = self._factories.get(name)
        if factory is None:
            raise NotFoundError(f"No tool registered under '{name}'.")
        return factory(environment)

    async def invoke(
        self, name: str, environment: BaseEnvironment, arguments: dict[str, object]
    ) -> ToolInvocationResult:
        """Run the full tool invocation lifecycle: validate, execute, serialize.

        Matches PROJECT_SPEC_2 SS67 / PROJECT_SPEC_6 SS48: validation failures and execution
        failures are both captured onto the returned :class:`ToolInvocationResult` rather than
        raised, so a single tool failure never terminates the whole run
        (PROJECT_SPEC_2 SS110/SS53).
        """
        tool = self.create(name, environment)
        start = time.perf_counter()
        try:
            validated = await tool.validate(arguments)
            raw_result = await tool.execute(validated)
            output = tool.serialize_result(raw_result)
            return ToolInvocationResult(
                tool_name=name,
                arguments=arguments,
                validated_arguments=validated,
                output=output,
                status="completed",
                latency=time.perf_counter() - start,
            )
        except _RECOVERABLE_TOOL_FAILURES as exc:
            return ToolInvocationResult(
                tool_name=name,
                arguments=arguments,
                status="failed",
                error=str(exc),
                latency=time.perf_counter() - start,
            )


tool_registry = ToolRegistry()
"""Process-wide default registry instance, populated as each tool module is imported."""
