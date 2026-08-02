"""Banking benchmark environment (PROJECT_SPEC_1 SS29/SS56): accounts and transfers."""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.banking.environment import BankingEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["account_lookup", "bank_transfer"]


def register() -> None:
    """Register the Banking environment factory and its descriptive metadata."""
    environment_registry.register("banking", BankingEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="banking",
            description=(
                "Account balance lookup and funds transfer with balance enforcement; also the "
                "selective-memory/confidentiality benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["BankingEnvironment", "register", "TOOLSET"]
