"""Identity Documents benchmark environment (PROJECT_SPEC_1 SS29/SS56).

Record lookup and date-of-birth correction; hosts the direct-harmful-request refusal benchmark,
paired with an over-refusal calibration task.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.identity_documents.environment import IdentityDocumentsEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["identity_lookup", "update_date_of_birth"]


def register() -> None:
    """Register the Identity Documents environment factory and its descriptive metadata."""
    environment_registry.register("identity_documents", IdentityDocumentsEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="identity_documents",
            description=(
                "Identity record lookup and date-of-birth correction; the direct-harmful-request "
                "refusal benchmark, paired with an over-refusal calibration task."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["IdentityDocumentsEnvironment", "register", "TOOLSET"]
