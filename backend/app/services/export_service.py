"""``ExportService`` (PROJECT_SPEC_2 SS91/SS100): JSON, Markdown, and CSV report exports.

Every export is generated exclusively from already-persisted traces and evaluation results
(PROJECT_SPEC_2 SS91) -- it never re-runs anything.
"""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.repositories.evaluation_repository import (
    EvaluationReportRepository,
    EvaluationScoreRepository,
)
from app.repositories.run_repository import RunRepository
from app.repositories.trace_repository import TraceRepository
from app.services.base import BaseService


class ExportService(BaseService):
    """Renders a run's persisted trace and evaluation data into JSON, Markdown, or CSV."""

    def __init__(
        self,
        run_repository: RunRepository,
        trace_repository: TraceRepository,
        evaluation_report_repository: EvaluationReportRepository,
        evaluation_score_repository: EvaluationScoreRepository,
    ) -> None:
        """Bind the service to the repositories it reads persisted data from."""
        self._run_repository = run_repository
        self._trace_repository = trace_repository
        self._evaluation_report_repository = evaluation_report_repository
        self._evaluation_score_repository = evaluation_score_repository

    async def export_json(self, run_id: int) -> dict[str, object]:
        """Export the full execution trace as a JSON-serializable ``dict``."""
        trace = await self._trace_repository.load_by_run(run_id)
        if trace is None:
            raise NotFoundError(f"No execution trace persisted for run_id {run_id}.")
        return dict(trace.trace_json)

    async def export_markdown(self, run_id: int) -> str:
        """Render a human-readable Markdown trust report for ``run_id``."""
        run = await self._run_repository.get(run_id)
        if run is None:
            raise NotFoundError(f"No run with id {run_id}.")
        trace = await self._trace_repository.load_by_run(run_id)
        report = await self._evaluation_report_repository.get_by_run(run_id)
        scores = await self._evaluation_score_repository.list_by_run(run_id)

        lines = [
            f"# AgentAudit Report: Run {run.run_uuid}",
            "",
            f"- **Provider**: {run.provider} / {run.model}",
            f"- **Environment**: {run.environment}",
            f"- **Status**: {run.status}",
            "",
        ]
        if report is not None:
            lines += [
                "## Composite Trust Score",
                "",
                f"**CTS (reported, capped)**: {report.cts_reported:.2f}/100",
                f"**CTS (raw, uncapped)**: {report.cts_raw:.2f}/100",
            ]
            if report.critical_failure:
                lines.append(
                    "**CRITICAL FAILURE**: capped by "
                    + ", ".join(report.critical_failure_modules)
                )
            lines += ["", report.overall_summary, ""]
        if scores:
            lines += [
                "## Evaluator Scores",
                "",
                "| Evaluator | Score | Confidence | Rubric Level |",
                "|---|---|---|---|",
            ]
            lines += [
                f"| {score.evaluator_name} | {score.score:.1f} | {score.confidence:.2f} | "
                f"{score.rubric_level} |"
                for score in scores
            ]
            lines.append("")
        if trace is not None:
            final_response = trace.trace_json.get("final_response", "N/A")
            lines += ["## Final Response", "", str(final_response), ""]
        return "\n".join(lines)

    async def export_csv(self, run_id: int) -> str:
        """Render evaluator scores as CSV for ``run_id``."""
        scores = await self._evaluation_score_repository.list_by_run(run_id)
        rows = ["evaluator_name,score,confidence,rubric_level"]
        rows += [
            f"{score.evaluator_name},{score.score},{score.confidence},{score.rubric_level}"
            for score in scores
        ]
        return "\n".join(rows)
