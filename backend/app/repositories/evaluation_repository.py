"""Evaluation-side repositories (PROJECT_SPEC_1 SS85-88).

Created in Phase 3 alongside every other repository (docs/adr/0007-full-schema-upfront.md), but
not exercised by any service until Phase 9's ``EvaluationService`` exists -- nothing in the
execution path (Phases 4-8) imports from this module, preserving execution/evaluation
decoupling (PROJECT_SPEC_1 SS106).
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, func, select

from app.models.behaviour_report import BehaviourReportModel
from app.models.evaluation_report import EvaluationReportModel
from app.models.evaluation_score import EvaluationScoreModel
from app.models.failure_report import FailureReportModel
from app.repositories.base import BaseRepository


class EvaluationReportRepository(BaseRepository[EvaluationReportModel]):
    """Persistence for :class:`~app.models.evaluation_report.EvaluationReportModel`."""

    model = EvaluationReportModel

    async def get_by_run(self, run_id: int) -> EvaluationReportModel | None:
        """Return the evaluation report for ``run_id``, or ``None``."""
        return await self.find_one(run_id=run_id)

    async def delete_by_run(self, run_id: int) -> None:
        """Delete the evaluation report for ``run_id``, if one exists.

        Called by ``EvaluationService._persist`` before inserting a fresh report, so
        re-evaluating an already-evaluated run (``POST /runs/{id}/evaluate`` is explicitly
        documented as re-runnable) replaces it instead of colliding with the ``run_id`` unique
        constraint. Only ever removes evaluation output, never the underlying execution trace.
        """
        stmt = delete(EvaluationReportModel).where(EvaluationReportModel.run_id == run_id)
        await self.session.execute(stmt)

    async def average_cts_raw(self) -> float | None:
        """Return the mean uncapped CTS across every persisted evaluation report, or ``None`` if
        empty.

        Deliberately averages ``cts_raw``, never ``cts_reported``: the reported value is clamped
        to 30 on a critical failure, so a mean over it would be a mean over clamped numbers and
        not interpretable (docs/adr/0008-cts-cap-is-policy-not-metric.md).
        """
        result = await self.session.execute(select(func.avg(EvaluationReportModel.cts_raw)))
        value = result.scalar_one()
        return float(value) if value is not None else None


class EvaluationScoreRepository(BaseRepository[EvaluationScoreModel]):
    """Persistence for :class:`~app.models.evaluation_score.EvaluationScoreModel`.

    Adding a new evaluator requires inserting only additional rows here -- never a schema
    migration (PROJECT_SPEC_1 SS86).
    """

    model = EvaluationScoreModel

    async def list_by_run(self, run_id: int) -> Sequence[EvaluationScoreModel]:
        """Return every evaluator's score for ``run_id``."""
        stmt = select(EvaluationScoreModel).where(EvaluationScoreModel.run_id == run_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_run_and_evaluator(
        self, run_id: int, evaluator_name: str
    ) -> EvaluationScoreModel | None:
        """Return one evaluator's score for ``run_id``, or ``None``."""
        return await self.find_one(run_id=run_id, evaluator_name=evaluator_name)

    async def delete_by_run(self, run_id: int) -> None:
        """Delete every evaluator's score for ``run_id``, if any exist (see
        ``EvaluationReportRepository.delete_by_run`` for why)."""
        stmt = delete(EvaluationScoreModel).where(EvaluationScoreModel.run_id == run_id)
        await self.session.execute(stmt)

    async def average_by_evaluator(self) -> list[dict[str, object]]:
        """Return ``[{evaluator_name, average_score, average_confidence, count}, ...]``."""
        stmt = select(
            EvaluationScoreModel.evaluator_name,
            func.avg(EvaluationScoreModel.score),
            func.avg(EvaluationScoreModel.confidence),
            func.count(),
        ).group_by(EvaluationScoreModel.evaluator_name)
        result = await self.session.execute(stmt)
        return [
            {
                "evaluator_name": name,
                "average_score": float(avg_score),
                "average_confidence": float(avg_confidence),
                "count": count,
            }
            for name, avg_score, avg_confidence, count in result.all()
        ]


class BehaviourReportRepository(BaseRepository[BehaviourReportModel]):
    """Persistence for :class:`~app.models.behaviour_report.BehaviourReportModel`."""

    model = BehaviourReportModel

    async def get_by_run(self, run_id: int) -> BehaviourReportModel | None:
        """Return the behavioural classification for ``run_id``, or ``None``."""
        return await self.find_one(run_id=run_id)

    async def delete_by_run(self, run_id: int) -> None:
        """Delete the behaviour report for ``run_id``, if one exists (see
        ``EvaluationReportRepository.delete_by_run`` for why)."""
        stmt = delete(BehaviourReportModel).where(BehaviourReportModel.run_id == run_id)
        await self.session.execute(stmt)


class FailureReportRepository(BaseRepository[FailureReportModel]):
    """Persistence for :class:`~app.models.failure_report.FailureReportModel`."""

    model = FailureReportModel

    async def get_by_run(self, run_id: int) -> FailureReportModel | None:
        """Return the failure attribution for ``run_id``, or ``None``."""
        return await self.find_one(run_id=run_id)

    async def delete_by_run(self, run_id: int) -> None:
        """Delete the failure report for ``run_id``, if one exists (see
        ``EvaluationReportRepository.delete_by_run`` for why)."""
        stmt = delete(FailureReportModel).where(FailureReportModel.run_id == run_id)
        await self.session.execute(stmt)
