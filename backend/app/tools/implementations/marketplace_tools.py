"""Marketplace environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class ProductSearchTool(EnvironmentActionTool):
    name = "product_search"
    description = "Search the product catalog by name."
    environment_name = "marketplace"
    action_name = "product_search"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }


class PlaceOrderTool(EnvironmentActionTool):
    name = "place_order"
    description = "Place an order for a given quantity of a product."
    environment_name = "marketplace"
    action_name = "place_order"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["product_id", "quantity"],
        }


class RedeemGiftcardTool(EnvironmentActionTool):
    name = "redeem_giftcard"
    description = "Redeem a stored gift card balance using a promo code."
    environment_name = "marketplace"
    action_name = "redeem_giftcard"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["code", "amount"],
        }


def register() -> None:
    """Register every Marketplace tool factory on the shared tool registry."""
    tool_registry.register("product_search", ProductSearchTool)
    tool_registry.register("place_order", PlaceOrderTool)
    tool_registry.register("redeem_giftcard", RedeemGiftcardTool)
