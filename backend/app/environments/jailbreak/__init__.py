"""Jailbreak benchmark environment (PROJECT_SPEC_1 SS29/SS56).

Account status lookup and wire transfer; the roleplay/authority-override jailbreak benchmark.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.jailbreak.environment import JailbreakEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["account_status", "wire_transfer"]


def register() -> None:
    """Register the Jailbreak environment factory and its descriptive metadata."""
    environment_registry.register("jailbreak", JailbreakEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="jailbreak",
            description=(
                "Account status lookup and wire transfer; the roleplay/authority-override "
                "jailbreak benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["JailbreakEnvironment", "register", "TOOLSET"]
