"""``validate_arguments_against_schema`` (PROJECT_SPEC_2 SS68)."""

from __future__ import annotations

import pytest

from app.core.exceptions import ToolError
from app.tools.validation import validate_arguments_against_schema

_SCHEMA = {
    "type": "object",
    "properties": {"origin": {"type": "string"}, "count": {"type": "integer"}},
    "required": ["origin"],
}


class TestValidateArgumentsAgainstSchema:
    def test_valid_arguments_pass_through_unchanged(self) -> None:
        args = {"origin": "NYC", "count": 2}
        assert validate_arguments_against_schema(_SCHEMA, args, tool_name="t") == args

    def test_missing_required_field_raises_tool_error(self) -> None:
        with pytest.raises(ToolError):
            validate_arguments_against_schema(_SCHEMA, {"count": 2}, tool_name="t")

    def test_wrong_type_raises_tool_error(self) -> None:
        with pytest.raises(ToolError):
            validate_arguments_against_schema(
                _SCHEMA, {"origin": "NYC", "count": "two"}, tool_name="t"
            )

    def test_unknown_extra_properties_are_ignored(self) -> None:
        args = {"origin": "NYC", "extra": "whatever"}
        result = validate_arguments_against_schema(_SCHEMA, args, tool_name="t")
        assert result["extra"] == "whatever"
