"""Payments environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class InvoiceLookupTool(EnvironmentActionTool):
    name = "invoice_lookup"
    description = "Look up an invoice's amount due, vendor account, and notes."
    environment_name = "payments"
    action_name = "invoice_lookup"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"invoice_id": {"type": "string"}},
            "required": ["invoice_id"],
        }


class SendPaymentTool(EnvironmentActionTool):
    name = "send_payment"
    description = "Send a payment of a given amount to an account."
    environment_name = "payments"
    action_name = "send_payment"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to_account": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["to_account", "amount"],
        }


def register() -> None:
    """Register every Payments tool factory on the shared tool registry."""
    tool_registry.register("invoice_lookup", InvoiceLookupTool)
    tool_registry.register("send_payment", SendPaymentTool)
