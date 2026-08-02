"""Cross-environment contract tests: every environment satisfies BaseEnvironment identically.

Ensures new environments can be added without the runner (or these tests) needing environment-
specific special-casing (PROJECT_SPEC_1 SS107/PROJECT_SPEC_2 SS61).
"""

from __future__ import annotations

import pytest

from app.core.exceptions import BenchmarkEnvironmentError
from app.environments.banking.environment import BankingEnvironment
from app.environments.email_env.environment import EmailEnvironment
from app.environments.identity_documents.environment import IdentityDocumentsEnvironment
from app.environments.jailbreak.environment import JailbreakEnvironment
from app.environments.marketplace.environment import MarketplaceEnvironment
from app.environments.memory_poisoning.environment import MemoryPoisoningEnvironment
from app.environments.payments.environment import PaymentsEnvironment
from app.environments.trip_planner.environment import TripPlannerEnvironment

ALL_ENVIRONMENT_CLASSES = [
    BankingEnvironment,
    PaymentsEnvironment,
    MarketplaceEnvironment,
    TripPlannerEnvironment,
    EmailEnvironment,
    IdentityDocumentsEnvironment,
    JailbreakEnvironment,
    MemoryPoisoningEnvironment,
]


@pytest.mark.asyncio
@pytest.mark.parametrize("environment_cls", ALL_ENVIRONMENT_CLASSES)
class TestEnvironmentContract:
    async def test_starts_incomplete_after_initialize(self, environment_cls: type) -> None:
        env = environment_cls()
        await env.initialize()
        assert await env.is_complete() is False

    async def test_observe_and_export_state_return_dicts(self, environment_cls: type) -> None:
        env = environment_cls()
        await env.initialize()
        assert isinstance(await env.observe(), dict)
        assert isinstance(await env.export_state(), dict)

    async def test_unknown_action_raises_benchmark_environment_error(
        self, environment_cls: type
    ) -> None:
        env = environment_cls()
        await env.initialize()
        assert await env.validate_action("definitely-not-a-real-action", {}) is False
        with pytest.raises(BenchmarkEnvironmentError):
            await env.step("definitely-not-a-real-action", {})

    async def test_reset_does_not_raise(self, environment_cls: type) -> None:
        env = environment_cls()
        await env.initialize()
        await env.reset()

    async def test_cleanup_does_not_raise(self, environment_cls: type) -> None:
        env = environment_cls()
        await env.initialize()
        await env.cleanup()
