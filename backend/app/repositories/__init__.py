"""Persistence-only repositories (PROJECT_SPEC_2 SS18/SS83-84).

CRUD + queries, no business logic.
"""

from app.repositories.base import BaseRepository
from app.repositories.benchmark_repository import (
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
    BenchmarkToolRepository,
)
from app.repositories.evaluation_repository import (
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.provider_repository import ProviderRepository
from app.repositories.run_repository import RunRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.tool_call_repository import ToolCallRepository, ToolOutputRepository
from app.repositories.trace_event_repository import TraceEventRepository
from app.repositories.trace_repository import TraceRepository

__all__ = [
    "BaseRepository",
    "BenchmarkEnvironmentRepository",
    "BenchmarkTaskRepository",
    "BenchmarkToolRepository",
    "BehaviourReportRepository",
    "EvaluationReportRepository",
    "EvaluationScoreRepository",
    "FailureReportRepository",
    "ProviderRepository",
    "RunRepository",
    "SettingsRepository",
    "ToolCallRepository",
    "ToolOutputRepository",
    "TraceEventRepository",
    "TraceRepository",
]
