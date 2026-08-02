"""Provider endpoints (PROJECT_SPEC_2 SS101): metadata only, never secrets."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import ProviderServiceDep
from app.config import Settings, get_settings
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=StandardResponse[list[str]])
async def list_providers(service: ProviderServiceDep) -> StandardResponse[list[str]]:
    """List every provider name registered on the :class:`ProviderFactory`."""
    return StandardResponse(data=service.supported_providers())


@router.get("/models", response_model=StandardResponse[list[dict[str, object]]])
async def list_provider_models(
    service: ProviderServiceDep, settings: Settings = Depends(get_settings)
) -> StandardResponse[list[dict[str, object]]]:
    """List models available through the currently configured AUT provider."""
    models = await service.list_aut_models(settings)
    return StandardResponse(data=[model.model_dump(mode="json") for model in models])


@router.get("/health", response_model=StandardResponse[dict[str, object]])
async def provider_health(
    service: ProviderServiceDep, settings: Settings = Depends(get_settings)
) -> StandardResponse[dict[str, object]]:
    """Run a live health check against both the configured AUT and Judge providers."""
    aut_health = await service.check_aut_health(settings)
    judge_health = await service.check_judge_health(settings)
    return StandardResponse(
        data={
            "aut": aut_health.model_dump(mode="json"),
            "judge": judge_health.model_dump(mode="json"),
        }
    )
