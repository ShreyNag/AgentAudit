"""Payments benchmark environment (PROJECT_SPEC_1 SS29/SS56): invoice lookup and payment.

Also the prompt-injection amount-tampering benchmark.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.payments.environment import PaymentsEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["invoice_lookup", "send_payment"]


def register() -> None:
    """Register the Payments environment factory and its descriptive metadata."""
    environment_registry.register("payments", PaymentsEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="payments",
            description=(
                "Invoice lookup and payment sending; the prompt-injection amount-tampering "
                "benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["PaymentsEnvironment", "register", "TOOLSET"]
