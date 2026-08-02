"""Evaluation endpoints (PROJECT_SPEC_2 SS97): historical traces may be re-evaluated."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import EvaluationServiceDep
from app.config import get_settings
from app.evaluation.rubric.loader import RubricLoader
from app.evaluation.scoring.cts import trust_level_for
from app.schemas.common import StandardResponse
from app.schemas.evaluation import (
    BehaviourReportResponse,
    CTSResponse,
    EvaluationReportResponse,
    EvaluationScoreResponse,
    FailureReportResponse,
    RubricResponse,
)

router = APIRouter(prefix="/runs", tags=["evaluation"])
# Deliberately its own router with no "/runs" prefix: a static "/runs/rubrics" path would collide
# with "/runs/{run_id}" (FastAPI/Starlette match by path shape first, so "rubrics" would be handed
# to run_id's int converter and 422 rather than falling through to this route).
rubric_router = APIRouter(prefix="/evaluators", tags=["evaluation"])


@router.post("/{run_id}/evaluate", response_model=StandardResponse[EvaluationReportResponse])
async def evaluate_run(
    run_id: int, service: EvaluationServiceDep
) -> StandardResponse[EvaluationReportResponse]:
    """Evaluate (or re-evaluate) the persisted trace for ``run_id``.

    Re-running this endpoint against a historical run re-evaluates it without re-executing the
    original agent (PROJECT_SPEC_1 SS98/SS106).
    """
    outcome = await service.evaluate_run(run_id, get_settings())
    report = await service.get_report(run_id)
    return StandardResponse(
        message=f"Evaluation complete: CTS {outcome.cts.cts:.2f} ({outcome.cts.trust_level}).",
        data=EvaluationReportResponse.model_validate(report),
    )


@router.get("/{run_id}/evaluation", response_model=StandardResponse[list[EvaluationScoreResponse]])
async def get_evaluation_scores(
    run_id: int, service: EvaluationServiceDep
) -> StandardResponse[list[EvaluationScoreResponse]]:
    """Return every evaluator's persisted score for ``run_id``."""
    scores = await service.get_scores(run_id)
    return StandardResponse(data=[EvaluationScoreResponse.model_validate(s) for s in scores])


@router.get("/{run_id}/cts", response_model=StandardResponse[CTSResponse])
async def get_cts(run_id: int, service: EvaluationServiceDep) -> StandardResponse[CTSResponse]:
    """Return the Composite Trust Score for ``run_id``."""
    report = await service.get_report(run_id)
    return StandardResponse(
        data=CTSResponse(run_id=run_id, cts=report.cts, trust_level=trust_level_for(report.cts))
    )


@router.get("/{run_id}/behaviour", response_model=StandardResponse[BehaviourReportResponse])
async def get_behaviour(
    run_id: int, service: EvaluationServiceDep
) -> StandardResponse[BehaviourReportResponse]:
    """Return the behavioural classification for ``run_id``."""
    behaviour = await service.get_behaviour(run_id)
    return StandardResponse(data=BehaviourReportResponse.model_validate(behaviour))


@router.get("/{run_id}/failure", response_model=StandardResponse[FailureReportResponse])
async def get_failure(
    run_id: int, service: EvaluationServiceDep
) -> StandardResponse[FailureReportResponse]:
    """Return the failure attribution for ``run_id``.

    Raises:
        NotFoundError: if the run was not evaluated, or had no attributable failure.
    """
    failure = await service.get_failure(run_id)
    return StandardResponse(data=FailureReportResponse.model_validate(failure))


@rubric_router.get("/rubrics", response_model=StandardResponse[dict[str, RubricResponse]])
async def get_rubrics() -> StandardResponse[dict[str, RubricResponse]]:
    """Return every evaluator's scoring rubric (criteria + five-level scale).

    Static reference data, independent of any run -- lets the UI show a reviewer what each score
    was actually judged against, not just the number itself.
    """
    loader = RubricLoader()
    return StandardResponse(
        data={
            name: RubricResponse.model_validate(loader.get(name))
            for name in loader.list_evaluator_names()
        }
    )
