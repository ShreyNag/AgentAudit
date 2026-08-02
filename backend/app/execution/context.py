"""``ExecutionContext`` (PROJECT_SPEC_6 SS37): the shared runtime object for one execution.

Passed explicitly to execution components rather than accessed globally (PROJECT_SPEC_6 SS22).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.benchmark.models import Task
from app.environments.base import BaseEnvironment
from app.execution.config import ExecutionConfig
from app.execution.state import ExecutionState
from app.providers.base import BaseProvider
from app.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from app.trace.recorder import TraceRecorder


class ExecutionContext:
    """Everything one execution needs, bound together for its lifetime."""

    def __init__(
        self,
        *,
        run_uuid: str,
        task: Task,
        environment: BaseEnvironment,
        provider: BaseProvider,
        tool_registry: ToolRegistry,
        trace_recorder: TraceRecorder,
        available_tools: list[str],
        config: ExecutionConfig,
    ) -> None:
        """Bind a run's task, environment, provider, tools, and trace recorder together."""
        self.run_uuid = run_uuid
        self.task = task
        self.environment = environment
        self.provider = provider
        self.tool_registry = tool_registry
        self.trace_recorder = trace_recorder
        self.available_tools = available_tools
        self.config = config
        self.state = ExecutionState()
        self.memory: dict[str, Any] = {}
