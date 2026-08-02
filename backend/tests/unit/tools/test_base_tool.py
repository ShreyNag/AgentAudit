"""``BaseTool``/``EnvironmentActionTool`` default behavior (ADR-003)."""

from __future__ import annotations

import pytest

from app.environments.banking.environment import BankingEnvironment
from app.tools.implementations.banking_tools import AccountLookupTool, BankTransferTool


@pytest.fixture
async def banking_env() -> BankingEnvironment:
    env = BankingEnvironment()
    await env.initialize()
    return env


@pytest.mark.asyncio
class TestBaseToolDefaults:
    async def test_schema_is_an_alias_for_parameters(self, banking_env: BankingEnvironment) -> None:
        tool = AccountLookupTool(banking_env)
        assert tool.schema() == tool.parameters()

    async def test_metadata_reports_the_full_contract(
        self, banking_env: BankingEnvironment
    ) -> None:
        tool = AccountLookupTool(banking_env)
        metadata = tool.metadata()
        assert metadata["name"] == "account_lookup"
        assert metadata["environment"] == "banking"
        assert "input_schema" in metadata

    async def test_default_reset_and_health_check(self, banking_env: BankingEnvironment) -> None:
        tool = AccountLookupTool(banking_env)
        await tool.reset()  # must not raise
        assert await tool.health_check() is True

    async def test_environment_action_tool_dispatches_to_step(
        self, banking_env: BankingEnvironment
    ) -> None:
        tool = BankTransferTool(banking_env)
        validated = await tool.validate(
            {"from_account": "acct-1", "to_account": "acct-4", "amount": 50.0}
        )
        result = await tool.execute(validated)
        assert result["status"] == "completed"

    async def test_environment_action_tool_validation_rejects_missing_field(
        self, banking_env: BankingEnvironment
    ) -> None:
        from app.core.exceptions import ToolError

        tool = BankTransferTool(banking_env)
        with pytest.raises(ToolError):
            await tool.validate({})
