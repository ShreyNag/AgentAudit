"""Tool system: pluggable, environment-scoped tools the Agent Under Test can invoke.

Every tool inherits :class:`~app.tools.base.BaseTool`; the runner never imports concrete tools
directly, it queries :class:`~app.tools.registry.ToolRegistry` (PROJECT_SPEC_1 SS30-31).
"""

from app.tools.base import BaseTool, EnvironmentActionTool
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.schemas import ToolInvocationResult

__all__ = [
    "BaseTool",
    "EnvironmentActionTool",
    "ToolRegistry",
    "tool_registry",
    "ToolInvocationResult",
]
