"""``EnvironmentRegistry`` / Environment Manager (PROJECT_SPEC_1 SS58, PROJECT_SPEC_2 SS58).

Instantiates fresh, isolated :class:`~app.environments.base.BaseEnvironment` instances by name.
The runner queries this registry instead of importing concrete environments directly
(PROJECT_SPEC_1 SS54/SS107), so new environments register without any runner change.
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.exceptions import NotFoundError
from app.environments.base import BaseEnvironment

EnvironmentFactory = Callable[[], BaseEnvironment]


class EnvironmentRegistry:
    """Registry of environment factories, keyed by environment name."""

    def __init__(self) -> None:
        """Start with an empty registry; concrete environments register at import time."""
        self._factories: dict[str, EnvironmentFactory] = {}

    def register(self, name: str, factory: EnvironmentFactory) -> None:
        """Register (or replace) the factory used to construct environment ``name``."""
        self._factories[name] = factory

    def list_environments(self) -> list[str]:
        """Return every registered environment name."""
        return sorted(self._factories)

    def is_registered(self, name: str) -> bool:
        """Return whether ``name`` has a registered factory."""
        return name in self._factories

    async def create(self, name: str) -> BaseEnvironment:
        """Construct and initialize a fresh instance of environment ``name``.

        Every benchmark run receives a brand-new instance so no state leaks across runs
        (PROJECT_SPEC_1 SS61).

        Raises:
            NotFoundError: if no environment is registered under ``name``.
        """
        factory = self._factories.get(name)
        if factory is None:
            raise NotFoundError(f"No environment registered under '{name}'.")
        environment = factory()
        await environment.initialize()
        return environment


environment_registry = EnvironmentRegistry()
"""Process-wide default registry instance, populated as each environment module is imported."""
