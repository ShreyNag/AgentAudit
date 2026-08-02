"""``BenchmarkRegistry`` (PROJECT_SPEC_2 SS54)."""

from __future__ import annotations

import pytest

from app.benchmark.models import BenchmarkEnvironmentMeta
from app.benchmark.registry import BenchmarkRegistry
from app.core.exceptions import NotFoundError


class TestBenchmarkRegistry:
    def test_register_and_get(self) -> None:
        registry = BenchmarkRegistry()
        registry.register(BenchmarkEnvironmentMeta(name="travel", description="d"))
        assert registry.get("travel").name == "travel"

    def test_get_unknown_raises_not_found(self) -> None:
        registry = BenchmarkRegistry()
        with pytest.raises(NotFoundError):
            registry.get("unknown")

    def test_list_all_and_is_registered(self) -> None:
        registry = BenchmarkRegistry()
        assert registry.is_registered("travel") is False
        registry.register(BenchmarkEnvironmentMeta(name="travel", description="d"))
        assert registry.is_registered("travel") is True
        assert len(registry.list_all()) == 1

    def test_shared_registry_has_all_eight_environments(self) -> None:
        import app.environments  # noqa: F401 - triggers registration
        from app.benchmark.registry import benchmark_registry

        names = {meta.name for meta in benchmark_registry.list_all()}
        expected = {
            "banking",
            "payments",
            "marketplace",
            "trip_planner",
            "email",
            "identity_documents",
            "jailbreak",
            "memory_poisoning",
        }
        assert expected.issubset(names)
