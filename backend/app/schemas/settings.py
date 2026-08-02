"""Settings request/response schemas (PROJECT_SPEC_2 SS102)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict


class SystemSettingResponse(BaseModel):
    """A single persisted, non-secret configuration value."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: Any
    description: str | None = None
    updated_at: dt.datetime


class SettingUpdateRequest(BaseModel):
    """Request body for ``PUT /api/v1/settings``."""

    key: str
    value: Any
    description: str | None = None
