"""``ToolRegistry`` create/invoke lifecycle (PROJECT_SPEC_2 SS67, PROJECT_SPEC_6 SS46/SS48)."""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError, ToolError
from app.environments.banking.environment import BankingEnvironment
from app.tools.implementations.banking_tools import AccountLookupTool, BankTransferTool
from app.tools.registry import ToolRegistry


@pytest.fixture
async def banking_env() -> BankingEnvironment:
    env = BankingEnvironment()
    await env.initialize()
    return env


@pytest.fixture
def registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("account_lookup", AccountLookupTool)
    registry.register("bank_transfer", BankTransferTool)
    return registry


@pytest.mark.asyncio
class TestToolRegistry:
    async def test_invoke_success_returns_completed_result(
        self, registry: ToolRegistry, banking_env: BankingEnvironment
    ) -> None:
        result = await registry.invoke("account_lookup", banking_env, {"account_id": "acct-1"})
        assert result.status == "completed"
        assert result.output["id"] == "acct-1"

    async def test_invoke_captures_tool_error_without_raising(
        self, registry: ToolRegistry, banking_env: BankingEnvironment
    ) -> None:
        result = await registry.invoke("bank_transfer", banking_env, {})  # missing required fields
        assert result.status == "failed"
        assert result.error is not None

    async def test_invoke_captures_environment_error_without_raising(
        self, registry: ToolRegistry, banking_env: BankingEnvironment
    ) -> None:
        result = await registry.invoke("account_lookup", banking_env, {"account_id": "nope"})
        assert result.status == "failed"
        assert "nope" in result.error

    async def test_create_unknown_tool_raises_not_found(
        self, registry: ToolRegistry, banking_env: BankingEnvironment
    ) -> None:
        with pytest.raises(NotFoundError):
            registry.create("does-not-exist", banking_env)

    def test_registering_the_same_name_to_a_different_factory_raises(
        self, registry: ToolRegistry
    ) -> None:
        with pytest.raises(ToolError):
            registry.register("account_lookup", BankTransferTool)

    def test_registering_the_same_name_to_the_same_factory_is_idempotent(
        self, registry: ToolRegistry
    ) -> None:
        registry.register("account_lookup", AccountLookupTool)  # must not raise
        assert "account_lookup" in registry.list_tools()
