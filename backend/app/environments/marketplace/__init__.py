"""Marketplace benchmark environment (PROJECT_SPEC_1 SS29/SS56): product search and ordering.

Also the tool-poisoning benchmark.
"""

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import benchmark_registry
from app.environments.marketplace.environment import MarketplaceEnvironment
from app.environments.registry import environment_registry

TOOLSET = ["product_search", "place_order", "redeem_giftcard"]


def register() -> None:
    """Register the Marketplace environment factory and its descriptive metadata."""
    environment_registry.register("marketplace", MarketplaceEnvironment)
    benchmark_registry.register(
        BenchmarkEnvironmentMeta(
            name="marketplace",
            description="Product search and ordering; the tool-poisoning benchmark.",
            toolset=TOOLSET,
        )
    )


__all__ = ["MarketplaceEnvironment", "register", "TOOLSET"]
