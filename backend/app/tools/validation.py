"""Lightweight JSON-Schema-subset argument validation (PROJECT_SPEC_2 SS68).

Deliberately not a full JSON Schema implementation (no external ``jsonschema`` dependency) --
only what PROJECT_SPEC_2 SS68 actually requires: required-field presence and basic type
checking. Tools needing richer validation may override :meth:`BaseTool.validate` entirely.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import ToolError

_JSON_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def validate_arguments_against_schema(
    schema: dict[str, Any], arguments: dict[str, Any], *, tool_name: str
) -> dict[str, Any]:
    """Validate ``arguments`` against a JSON-Schema-like ``{type, properties, required}`` dict.

    Raises:
        ToolError: if a required property is missing, or a provided property's type does not
            match its schema declaration.
    """
    required = schema.get("required", [])
    missing = [field for field in required if field not in arguments]
    if missing:
        raise ToolError(f"Tool '{tool_name}' is missing required arguments: {', '.join(missing)}.")

    properties: dict[str, Any] = schema.get("properties", {})
    for field, value in arguments.items():
        declared = properties.get(field)
        if declared is None:
            continue
        expected_type = _JSON_TYPE_MAP.get(declared.get("type", ""))
        if expected_type is not None and not isinstance(value, expected_type):
            raise ToolError(
                f"Tool '{tool_name}' argument '{field}' must be of type "
                f"'{declared.get('type')}', got '{type(value).__name__}'."
            )
    return arguments
