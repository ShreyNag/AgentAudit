"""Email benchmark environment (PROJECT_SPEC_1 SS29/SS56): inbox search and sending."""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.email_env.environment import EmailEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["email_search", "send_email"]


def register() -> None:
    """Register the Email environment factory and its descriptive metadata."""
    environment_registry.register("email", EmailEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="email",
            description=(
                "Inbox search and email sending over a seeded set of threads; also the indirect "
                "prompt-injection benchmark."
            ),
            toolset=TOOLSET,
        )
    )


__all__ = ["EmailEnvironment", "register", "TOOLSET"]
