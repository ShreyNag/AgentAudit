"""Shared response envelope used by every API endpoint (PROJECT_SPEC_2 SS16/SS104)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class StandardResponse(BaseModel, Generic[DataT]):
    """The single response shape every AgentAudit endpoint returns.

    Matches PROJECT_SPEC_2 SS104: ``{status, message, data, metadata, errors}``.
    """

    status: str = "success"
    message: str = ""
    data: DataT | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    errors: list[str] | None = None


class PaginationParams(BaseModel):
    """Standard pagination query parameters (PROJECT_SPEC_2 SS103)."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
    sort: str | None = None
    order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedMetadata(BaseModel):
    """Pagination metadata attached to list-endpoint responses."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
