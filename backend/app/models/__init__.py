"""SQLAlchemy ORM models: the 14 tables defined in PROJECT_SPEC_1 SS76-SS89.

Importing this package registers every model on :data:`app.database.base.Base.metadata`, which
is what Alembic's ``env.py`` uses as ``target_metadata`` for autogeneration (PROJECT_SPEC_6
ADR-006 in ``docs/adr/0006-alembic-location.md``).
"""

from app.database.base import Base
from app.models.behaviour_report import BehaviourReportModel
from app.models.benchmark_environment import BenchmarkEnvironmentModel
from app.models.benchmark_task import BenchmarkTaskModel
from app.models.benchmark_tool import BenchmarkToolModel
from app.models.evaluation_report import EvaluationReportModel
from app.models.evaluation_score import EvaluationScoreModel
from app.models.execution_trace import ExecutionTraceModel
from app.models.failure_report import FailureReportModel
from app.models.provider import ProviderModel
from app.models.run import RunModel
from app.models.system_settings import SystemSettingsModel
from app.models.tool_call import ToolCallModel
from app.models.tool_output import ToolOutputModel
from app.models.trace_event import TraceEventModel

__all__ = [
    "Base",
    "BehaviourReportModel",
    "BenchmarkEnvironmentModel",
    "BenchmarkTaskModel",
    "BenchmarkToolModel",
    "EvaluationReportModel",
    "EvaluationScoreModel",
    "ExecutionTraceModel",
    "FailureReportModel",
    "ProviderModel",
    "RunModel",
    "SystemSettingsModel",
    "ToolCallModel",
    "ToolOutputModel",
    "TraceEventModel",
]
