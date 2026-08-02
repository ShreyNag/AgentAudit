"""Export endpoints (PROJECT_SPEC_2 SS100): JSON, Markdown, CSV -- generated from persisted data."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.api.dependencies import ExportServiceDep
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/runs", tags=["exports"])


@router.get("/{run_id}/export/json", response_model=StandardResponse[dict[str, object]])
async def export_json(
    run_id: int, service: ExportServiceDep
) -> StandardResponse[dict[str, object]]:
    """Export the full execution trace as JSON."""
    return StandardResponse(data=await service.export_json(run_id))


@router.get("/{run_id}/export/markdown", response_class=PlainTextResponse)
async def export_markdown(run_id: int, service: ExportServiceDep) -> str:
    """Export a human-readable Markdown trust report."""
    return await service.export_markdown(run_id)


@router.get("/{run_id}/export/csv", response_class=PlainTextResponse)
async def export_csv(run_id: int, service: ExportServiceDep) -> str:
    """Export evaluator scores as CSV."""
    return await service.export_csv(run_id)
