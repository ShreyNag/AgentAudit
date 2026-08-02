"""Email environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class EmailSearchTool(EnvironmentActionTool):
    name = "email_search"
    description = "Search the inbox for messages matching a query."
    environment_name = "email"
    action_name = "email_search"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }


class SendEmailTool(EnvironmentActionTool):
    name = "send_email"
    description = "Send a new email."
    environment_name = "email"
    action_name = "send_email"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        }


def register() -> None:
    """Register every Email tool factory on the shared tool registry."""
    tool_registry.register("email_search", EmailSearchTool)
    tool_registry.register("send_email", SendEmailTool)
