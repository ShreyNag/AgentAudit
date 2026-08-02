"""Banking environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class AccountLookupTool(EnvironmentActionTool):
    name = "account_lookup"
    description = "Look up an account's current balance."
    environment_name = "banking"
    action_name = "account_lookup"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        }


class BankTransferTool(EnvironmentActionTool):
    name = "bank_transfer"
    description = "Transfer funds from one account to another."
    environment_name = "banking"
    action_name = "bank_transfer"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_account": {"type": "string"},
                "to_account": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["from_account", "to_account", "amount"],
        }


def register() -> None:
    """Register every Banking tool factory on the shared tool registry."""
    tool_registry.register("account_lookup", AccountLookupTool)
    tool_registry.register("bank_transfer", BankTransferTool)
