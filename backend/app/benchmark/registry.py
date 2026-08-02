"""``BenchmarkRegistry`` (PROJECT_SPEC_2 SS54): metadata catalog for benchmark environments.

Distinct from :class:`app.environments.registry.EnvironmentRegistry`, which holds the live,
instantiable :class:`~app.environments.base.BaseEnvironment` factories -- this registry only
tracks descriptive metadata (name, description, toolset, difficulty levels), used for discovery
and validation before an environment is actually instantiated.
"""

from __future__ import annotations

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.core.exceptions import NotFoundError


class BenchmarkRegistry:
    """In-memory registry of :class:`BenchmarkEnvironmentMeta` entries.

    New environments register themselves without any change to the runner or evaluation
    engine (PROJECT_SPEC_1 SS54/SS107).
    """

    def __init__(self) -> None:
        """Start with an empty registry; environments register themselves at import time."""
        self._entries: dict[str, BenchmarkEnvironmentMeta] = {}

    def register(self, meta: BenchmarkEnvironmentMeta) -> None:
        """Register (or replace) the metadata for one benchmark environment."""
        self._entries[meta.name] = meta

    def get(self, name: str) -> BenchmarkEnvironmentMeta:
        """Return the metadata for ``name``.

        Raises:
            NotFoundError: if no environment is registered under ``name``.
        """
        entry = self._entries.get(name)
        if entry is None:
            raise NotFoundError(f"No benchmark environment registered under '{name}'.")
        return entry

    def list_all(self) -> list[BenchmarkEnvironmentMeta]:
        """Return every registered environment's metadata."""
        return list(self._entries.values())

    def is_registered(self, name: str) -> bool:
        """Return whether an environment is registered under ``name``."""
        return name in self._entries


benchmark_registry = BenchmarkRegistry()
"""Process-wide default registry instance, populated by ``app.environments`` at import time."""
