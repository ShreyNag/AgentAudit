"""FastAPI dependency providers that assemble services from a request-scoped session.

Each factory function builds fresh repositories bound to the current request's
:class:`~sqlalchemy.ext.asyncio.AsyncSession` and hands them to the corresponding service
(PROJECT_SPEC_2 SS9/SS18-19).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies.database import DbSession
from app.repositories.benchmark_repository import (
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
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
from app.services.benchmark_service import BenchmarkService
from app.services.evaluation_service import EvaluationService
from app.services.execution_service import ExecutionService
from app.services.export_service import ExportService
from app.services.provider_service import ProviderService
from app.services.settings_service import SettingsService
from app.services.trace_service import TraceService


def get_benchmark_service(session: DbSession) -> BenchmarkService:
    """Build a :class:`BenchmarkService` bound to the current request's session."""
    return BenchmarkService(
        BenchmarkTaskRepository(session), BenchmarkEnvironmentRepository(session)
    )


def get_execution_service(session: DbSession) -> ExecutionService:
    """Build an :class:`ExecutionService` bound to the current request's session."""
    return ExecutionService(
        RunRepository(session),
        TraceRepository(session),
        TraceEventRepository(session),
        ToolCallRepository(session),
        ToolOutputRepository(session),
        BenchmarkTaskRepository(session),
    )


def get_trace_service(session: DbSession) -> TraceService:
    """Build a :class:`TraceService` bound to the current request's session."""
    return TraceService(TraceRepository(session), TraceEventRepository(session))


def get_provider_service(session: DbSession) -> ProviderService:
    """Build a :class:`ProviderService` bound to the current request's session."""
    return ProviderService(ProviderRepository(session))


def get_evaluation_service(session: DbSession) -> EvaluationService:
    """Build an :class:`EvaluationService` bound to the current request's session."""
    return EvaluationService(
        RunRepository(session),
        TraceRepository(session),
        BenchmarkTaskRepository(session),
        EvaluationReportRepository(session),
        EvaluationScoreRepository(session),
        BehaviourReportRepository(session),
        FailureReportRepository(session),
    )


def get_export_service(session: DbSession) -> ExportService:
    """Build an :class:`ExportService` bound to the current request's session."""
    return ExportService(
        RunRepository(session),
        TraceRepository(session),
        EvaluationReportRepository(session),
        EvaluationScoreRepository(session),
    )


def get_settings_service(session: DbSession) -> SettingsService:
    """Build a :class:`SettingsService` bound to the current request's session."""
    return SettingsService(SettingsRepository(session))


def get_run_repository(session: DbSession) -> RunRepository:
    """Build a bare :class:`RunRepository` for read-only run listing endpoints."""
    return RunRepository(session)


def get_settings_repository(session: DbSession) -> SettingsRepository:
    """Build a bare :class:`SettingsRepository` for the settings endpoints."""
    return SettingsRepository(session)


BenchmarkServiceDep = Annotated[BenchmarkService, Depends(get_benchmark_service)]
ExecutionServiceDep = Annotated[ExecutionService, Depends(get_execution_service)]
TraceServiceDep = Annotated[TraceService, Depends(get_trace_service)]
ProviderServiceDep = Annotated[ProviderService, Depends(get_provider_service)]
EvaluationServiceDep = Annotated[EvaluationService, Depends(get_evaluation_service)]
ExportServiceDep = Annotated[ExportService, Depends(get_export_service)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
RunRepositoryDep = Annotated[RunRepository, Depends(get_run_repository)]
SettingsRepositoryDep = Annotated[SettingsRepository, Depends(get_settings_repository)]
