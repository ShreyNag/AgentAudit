"""``EnvironmentRegistry`` isolation guarantees (PROJECT_SPEC_1 SS61)."""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError
from app.environments import environment_registry  # triggers registration of all 8 environments


@pytest.mark.asyncio
class TestEnvironmentRegistry:
    async def test_all_eight_environments_are_registered(self) -> None:
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
        assert expected.issubset(set(environment_registry.list_environments()))

    async def test_create_returns_an_initialized_environment(self) -> None:
        env = await environment_registry.create("banking")
        observation = await env.observe()
        assert observation["accounts"]["acct-1"] == 3200.00

    async def test_create_unknown_environment_raises_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await environment_registry.create("does-not-exist")

    async def test_each_create_call_returns_an_isolated_instance(self) -> None:
        first = await environment_registry.create("banking")
        second = await environment_registry.create("banking")
        await first.step(
            "bank_transfer", {"from_account": "acct-1", "to_account": "acct-4", "amount": 200.0}
        )
        assert await first.is_complete() is True
        assert await second.is_complete() is False
