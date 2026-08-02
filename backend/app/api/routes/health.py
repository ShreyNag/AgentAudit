"""Health endpoints (PROJECT_SPEC_2 SS21/SS93).

Report component status only -- never secrets or internal configuration.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import DbSession
from app.config import get_settings
from app.database.session import get_database
from app.providers.factory import ProviderFactory
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=StandardResponse[dict[str, str]])
async def health() -> StandardResponse[dict[str, str]]:
    """Liveness check: the process is up and configuration loaded successfully."""
    settings = get_settings()
    return StandardResponse(
        message="AgentAudit is running.",
        data={
            "application_version": settings.application_version,
            "framework_version": settings.framework_version,
        },
    )


@router.get("/database", response_model=StandardResponse[dict[str, bool]])
async def health_database(_session: DbSession) -> StandardResponse[dict[str, bool]]:
    """Readiness check for the database connection.

    Accepting ``_session`` as a dependency forces FastAPI to open (and therefore validate) a
    connection via the standard request-scoped session pathway before we additionally run an
    explicit connectivity probe below.
    """
    database = get_database()
    reachable = await database.check_connectivity()
    return StandardResponse(data={"reachable": reachable})


@router.get("/providers", response_model=StandardResponse[dict[str, list[str]]])
async def health_providers() -> StandardResponse[dict[str, list[str]]]:
    """Report which LLM providers are known to the :class:`ProviderFactory` registry.

    This reports registered provider *names*, not live connectivity for each -- checking
    connectivity would require constructing and authenticating a full adapter per provider on
    every health check, which is unnecessary request-time cost for a liveness probe.
    """
    return StandardResponse(data={"supported_providers": ProviderFactory.supported_providers()})


@router.get("/system", response_model=StandardResponse[dict[str, str]])
async def health_system() -> StandardResponse[dict[str, str]]:
    """Report overall system status without exposing sensitive configuration."""
    settings = get_settings()
    return StandardResponse(
        data={
            "status": "ok",
            "log_level": settings.log_level,
        }
    )
