"""Jailbreak environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class AccountStatusTool(EnvironmentActionTool):
    name = "account_status"
    description = "Look up an account's current balance and status."
    environment_name = "jailbreak"
    action_name = "account_status"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        }


class WireTransferTool(EnvironmentActionTool):
    name = "wire_transfer"
    description = "Wire funds from one account to another."
    environment_name = "jailbreak"
    action_name = "wire_transfer"

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
    """Register every Jailbreak tool factory on the shared tool registry."""
    tool_registry.register("account_status", AccountStatusTool)
    tool_registry.register("wire_transfer", WireTransferTool)
