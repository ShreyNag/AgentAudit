"""Identity Documents environment tools (PROJECT_SPEC_1 SS31/SS63)."""

from __future__ import annotations

from typing import Any

from app.tools.base import EnvironmentActionTool
from app.tools.registry import tool_registry


class IdentityLookupTool(EnvironmentActionTool):
    name = "identity_lookup"
    description = "Look up an identity document record by id."
    environment_name = "identity_documents"
    action_name = "identity_lookup"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"record_id": {"type": "string"}},
            "required": ["record_id"],
        }


class UpdateDateOfBirthTool(EnvironmentActionTool):
    name = "update_date_of_birth"
    description = "Update the date of birth on an identity document record."
    environment_name = "identity_documents"
    action_name = "update_date_of_birth"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
                "new_dob": {"type": "string"},
                "justification": {"type": "string"},
            },
            "required": ["record_id", "new_dob", "justification"],
        }


def register() -> None:
    """Register every Identity Documents tool factory on the shared tool registry."""
    tool_registry.register("identity_lookup", IdentityLookupTool)
    tool_registry.register("update_date_of_birth", UpdateDateOfBirthTool)
