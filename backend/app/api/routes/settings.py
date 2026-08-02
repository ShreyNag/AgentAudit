"""Settings endpoints (PROJECT_SPEC_2 SS102). Secrets are never returned."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SettingsServiceDep
from app.schemas.common import StandardResponse
from app.schemas.settings import SettingUpdateRequest, SystemSettingResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=StandardResponse[list[SystemSettingResponse]])
async def list_settings(
    service: SettingsServiceDep,
) -> StandardResponse[list[SystemSettingResponse]]:
    """List every persisted, non-secret setting."""
    settings = await service.list_all()
    return StandardResponse(data=[SystemSettingResponse.model_validate(s) for s in settings])


@router.put("", response_model=StandardResponse[SystemSettingResponse])
async def update_setting(
    request: SettingUpdateRequest, service: SettingsServiceDep
) -> StandardResponse[SystemSettingResponse]:
    """Create or update a single setting."""
    setting = await service.set(request.key, request.value, request.description)
    return StandardResponse(data=SystemSettingResponse.model_validate(setting))
