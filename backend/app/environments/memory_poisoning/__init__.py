"""Memory Poisoning benchmark environment (PROJECT_SPEC_1 SS29/SS56).

Audited account lookup and limit-enforced transfer; the planted-falsehood memory-poisoning
benchmark.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.memory_poisoning.environment import MemoryPoisoningEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["account_audit_lookup", "bank_transfer_limited"]


def register() -> None:
    """Register the Memory Poisoning environment factory and its descriptive metadata."""
    environment_registry.register("memory_poisoning", MemoryPoisoningEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="memory_poisoning",
            description=(
                "Audited account lookup and limit-enforced transfer; the planted-falsehood "
                "memory-poisoning benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["MemoryPoisoningEnvironment", "register", "TOOLSET"]
