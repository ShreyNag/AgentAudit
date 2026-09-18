"""Batch-run the full benchmark suite against several AUT models and store everything.

Purpose: for the paper's results section, run every seeded benchmark task against N
different models (e.g. 5), evaluate each run with the *same* Judge configuration (kept
constant across models so scores are comparable), and persist both a raw JSON blob per
run and a flattened CSV/JSONL row per run -- everything ``generate_report_figures.py``
needs, plus the full trace/evaluation JSON for anything not already captured in the CSV.

This script only reads the existing app/ package -- it does not modify any existing file
or any existing service/route. It talks to the same database the API uses, via the same
services (ExecutionService, EvaluationService, BenchmarkService, ExportService), wired up
by hand the way app/api/dependencies/services.py wires them for a request, since there is
no HTTP request here to hang a FastAPI dependency off of.

Usage (from the backend/ directory, with the venv that has the main + research
dependencies installed -- see scripts/research_requirements.txt):

    python scripts/run_benchmark_suite.py --config scripts/research_config.json

Re-running with the same --output-dir resumes: any (model, task) pair already recorded
with status "ok" in results.csv is skipped, so an interrupted batch (rate limit, crash,
Ctrl-C) can just be restarted.

Config file schema (see scripts/research_config.example.json):

    {
      "models": [
        {
          "label": "gpt-5",                 // short name used in every output file/column
          "provider": "openai",             // must be a name ProviderFactory recognizes
          "model": "gpt-5",
          "api_key": "sk-...",              // OR "api_key_env": "OPENAI_API_KEY"
          "base_url": "https://api.openai.com/v1",
          "timeout": 60                     // optional, defaults to AUT_TIMEOUT
        },
        ...
      ]
    }

The Judge (JUDGE_PROVIDER/JUDGE_MODEL/JUDGE_API_KEY in backend/.env) is deliberately NOT
overridden per model -- every model in the batch is graded by the same judge, which is
what makes the resulting scores comparable across models in the first place.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.config.settings import Settings  # noqa: E402
from app.core.exceptions import AgentAuditError, ConfigurationError, NotFoundError  # noqa: E402
from app.database.session import Database  # noqa: E402
from app.providers.exceptions import ProviderAuthenticationError  # noqa: E402
from app.repositories.benchmark_repository import (  # noqa: E402
    BenchmarkEnvironmentRepository,
    BenchmarkTaskRepository,
)
from app.repositories.evaluation_repository import (  # noqa: E402
    BehaviourReportRepository,
    EvaluationReportRepository,
    EvaluationScoreRepository,
    FailureReportRepository,
)
from app.repositories.run_repository import RunRepository  # noqa: E402
from app.repositories.tool_call_repository import (  # noqa: E402
    ToolCallRepository,
    ToolOutputRepository,
)
from app.repositories.trace_event_repository import TraceEventRepository  # noqa: E402
from app.repositories.trace_repository import TraceRepository  # noqa: E402
from app.services.benchmark_service import BenchmarkService  # noqa: E402
from app.services.evaluation_service import EvaluationService  # noqa: E402
from app.services.execution_service import ExecutionService  # noqa: E402
from app.services.export_service import ExportService  # noqa: E402

#: Canonical evaluator order (app/evaluation/evaluators/registry.py's build_default_registry),
#: used to give every results.csv row the same fixed set of score_<name>/confidence_<name>
#: columns regardless of which evaluators happened to complete for a given run.
EVALUATOR_NAMES: tuple[str, ...] = (
    "instruction_integrity",
    "planner",
    "memory",
    "tool_selection",
    "tool_invocation",
    "tool_correctness",
    "alignment",
    "tool_faithfulness",
    "security",
    "integrity",
)

#: Exceptions worth aborting the rest of a model's tasks over: things that are deterministically
#: true of the model's *configuration* (bad/missing API key, unregistered provider name, a task
#: id that doesn't exist) and will therefore fail identically on every remaining task. Everything
#: else -- rate limits after retries are exhausted, a Judge JSON hiccup, a malformed request from
#: one specific turn's conversation state -- is per-task and transient, so it must not cascade;
#: it is recorded as a normal per-task error and the batch moves on to the next task.
CONFIG_FATAL_EXCEPTIONS: tuple[type[Exception], ...] = (
    ConfigurationError,
    ProviderAuthenticationError,
    NotFoundError,
)

CSV_FIELDS: list[str] = [
    "batch_id",
    "recorded_at",
    "model_label",
    "provider",
    "model",
    "task_id",
    "environment",
    "difficulty",
    "attack_type",
    "run_id",
    "run_uuid",
    "status",
    "stage",
    "error_message",
    "execution_time_seconds",
    "cts_raw",
    "cts_reported",
    "critical_failure",
    "critical_failure_modules",
    "trust_level",
    "cts_confidence",
    "behaviour_classification",
    "behaviour_confidence",
    "primary_failure",
    "secondary_failures",
    *[f"score_{name}" for name in EVALUATOR_NAMES],
    *[f"confidence_{name}" for name in EVALUATOR_NAMES],
]


def _build_execution_service(session: AsyncSession) -> ExecutionService:
    """Mirror app/api/dependencies/services.py's get_execution_service for a bare session."""
    return ExecutionService(
        RunRepository(session),
        TraceRepository(session),
        TraceEventRepository(session),
        ToolCallRepository(session),
        ToolOutputRepository(session),
        BenchmarkTaskRepository(session),
    )


def _build_evaluation_service(session: AsyncSession) -> EvaluationService:
    """Mirror app/api/dependencies/services.py's get_evaluation_service for a bare session."""
    return EvaluationService(
        RunRepository(session),
        TraceRepository(session),
        BenchmarkTaskRepository(session),
        EvaluationReportRepository(session),
        EvaluationScoreRepository(session),
        BehaviourReportRepository(session),
        FailureReportRepository(session),
    )


def _build_export_service(session: AsyncSession) -> ExportService:
    """Mirror app/api/dependencies/services.py's get_export_service for a bare session."""
    return ExportService(
        RunRepository(session),
        TraceRepository(session),
        EvaluationReportRepository(session),
        EvaluationScoreRepository(session),
    )


def _build_benchmark_service(session: AsyncSession) -> BenchmarkService:
    """Mirror app/api/dependencies/services.py's get_benchmark_service for a bare session."""
    return BenchmarkService(
        BenchmarkTaskRepository(session), BenchmarkEnvironmentRepository(session)
    )


class SessionScope:
    """Standalone equivalent of app/database/session.py's get_db: commit-or-rollback-and-close.

    The FastAPI route layer gets this behavior for free from the get_db dependency; a bare
    script has no request to hang that off of, so it is reproduced here explicitly rather than
    leaving every call site to remember to commit.
    """

    def __init__(self, database: Database) -> None:
        self._database = database
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = self._database.session()
        return self._session

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        assert self._session is not None
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()


def resolve_model_settings(base_settings: Settings, model_cfg: dict[str, Any]) -> Settings:
    """Build a Settings override for one model config, leaving JUDGE_*/MYSQL_* untouched."""
    import os

    api_key = model_cfg.get("api_key")
    if not api_key:
        env_var = model_cfg.get("api_key_env")
        if env_var:
            api_key = os.environ.get(env_var, "")
    return base_settings.model_copy(
        update={
            "aut_provider": model_cfg["provider"],
            "aut_model": model_cfg["model"],
            "aut_api_key": api_key or "",
            "aut_base_url": model_cfg.get("base_url"),
            "aut_timeout": model_cfg.get("timeout", base_settings.aut_timeout),
        }
    )


def load_completed(results_csv: Path) -> set[tuple[str, str]]:
    """Return the (model_label, task_id) pairs already recorded with status "ok"."""
    if not results_csv.exists():
        return set()
    completed: set[tuple[str, str]] = set()
    with results_csv.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("status") == "ok":
                completed.add((row["model_label"], row["task_id"]))
    return completed


def append_csv_row(results_csv: Path, row: dict[str, Any]) -> None:
    is_new = not results_csv.exists()
    with results_csv.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def append_jsonl_row(results_jsonl: Path, row: dict[str, Any]) -> None:
    with results_jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def error_row(
    *,
    batch_id: str,
    model_label: str,
    model_cfg: dict[str, Any],
    task_id: str,
    environment: str,
    difficulty: str,
    attack_type: str | None,
    stage: str,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "model_label": model_label,
        "provider": model_cfg["provider"],
        "model": model_cfg["model"],
        "task_id": task_id,
        "environment": environment,
        "difficulty": difficulty,
        "attack_type": attack_type or "",
        "status": "error",
        "stage": stage,
        "error_message": f"{type(exc).__name__}: {exc}",
    }


async def run_one(
    *,
    database: Database,
    batch_id: str,
    output_dir: Path,
    model_label: str,
    model_cfg: dict[str, Any],
    model_settings: Settings,
    task_id: str,
    environment: str,
    difficulty: str,
    attack_type: str | None,
) -> dict[str, Any]:
    """Execute one (model, task) pair end-to-end and return its flattened results.csv row.

    Raises only for config-level errors worth aborting the rest of this model's tasks over
    (e.g. a bad API key caught on the very first call); per-task failures are caught and
    turned into an "error" row instead of raising, so one bad task does not stop the batch.
    """
    async with SessionScope(database) as session:
        execution_service = _build_execution_service(session)
        run_row, _result = await execution_service.launch(task_id=task_id, settings=model_settings)

    async with SessionScope(database) as session:
        evaluation_service = _build_evaluation_service(session)
        # model_settings only overrides the AUT_* fields (see resolve_model_settings) -- its
        # JUDGE_* fields are untouched copies of base_settings, so every model in the batch is
        # graded by the identical judge configuration and scores stay comparable across models.
        outcome = await evaluation_service.evaluate_run(run_row.id, model_settings)
        report = await evaluation_service.get_report(run_row.id)

    async with SessionScope(database) as session:
        export_service = _build_export_service(session)
        trace_export = await export_service.export_json(run_row.id)

    scores_by_name = {r.evaluator_name: r for r in outcome.evaluator_results}

    raw_record = {
        "batch_id": batch_id,
        "model_label": model_label,
        "provider": model_cfg["provider"],
        "model": model_cfg["model"],
        "run": {
            "id": run_row.id,
            "run_uuid": run_row.run_uuid,
            "status": run_row.status,
            "execution_time": run_row.execution_time,
            "environment": run_row.environment,
        },
        "task": {
            "task_id": task_id,
            "environment": environment,
            "difficulty": difficulty,
            "attack_type": attack_type,
        },
        "cts": outcome.cts.model_dump(mode="json"),
        "behaviour": outcome.behaviour.model_dump(mode="json"),
        "failure": outcome.failure.model_dump(mode="json") if outcome.failure else None,
        "evaluator_results": [r.model_dump(mode="json") for r in outcome.evaluator_results],
        "evaluation_report_summary": report.overall_summary,
        "trace": trace_export,
    }
    raw_dir = output_dir / "raw" / model_label
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{task_id}.json").write_text(
        json.dumps(raw_record, indent=2, default=str), encoding="utf-8"
    )

    row: dict[str, Any] = {
        "batch_id": batch_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "model_label": model_label,
        "provider": model_cfg["provider"],
        "model": model_cfg["model"],
        "task_id": task_id,
        "environment": environment,
        "difficulty": difficulty,
        "attack_type": attack_type or "",
        "run_id": run_row.id,
        "run_uuid": run_row.run_uuid,
        "status": "ok",
        "stage": "",
        "error_message": "",
        "execution_time_seconds": run_row.execution_time,
        # cts_raw (uncapped) is the analysis number -- use it for any mean/correlation/comparison
        # across rows. cts_reported (clamped to 30 on a hard-cap evaluator's critical failure) is
        # the decision number only -- see docs/adr/0008-cts-cap-is-policy-not-metric.md.
        "cts_raw": outcome.cts.cts_raw,
        "cts_reported": outcome.cts.cts_reported,
        "critical_failure": outcome.cts.critical_failure,
        "critical_failure_modules": ";".join(outcome.cts.critical_failure_modules),
        "trust_level": outcome.cts.trust_level,
        "cts_confidence": outcome.cts.confidence,
        "behaviour_classification": outcome.behaviour.classification,
        "behaviour_confidence": outcome.behaviour.confidence,
        "primary_failure": outcome.failure.primary_failure if outcome.failure else "",
        "secondary_failures": ";".join(outcome.failure.secondary_failures)
        if outcome.failure
        else "",
    }
    for name in EVALUATOR_NAMES:
        result = scores_by_name.get(name)
        row[f"score_{name}"] = result.score if result else ""
        row[f"confidence_{name}"] = result.confidence if result else ""
    return row


async def main_async(args: argparse.Namespace) -> None:
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    models: list[dict[str, Any]] = config["models"]
    if args.only_models:
        wanted = set(args.only_models.split(","))
        models = [m for m in models if m["label"] in wanted]

    base_settings = Settings()
    database = Database(base_settings)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_csv = output_dir / "results.csv"
    results_jsonl = output_dir / "results.jsonl"
    batch_id = args.batch_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    completed = load_completed(results_csv)
    print(
        f"[{batch_id}] output_dir={output_dir} ; {len(completed)} (model,task) pairs already done"
    )

    async with SessionScope(database) as session:
        benchmark_service = _build_benchmark_service(session)
        await benchmark_service.ensure_seeded()
        tasks = await benchmark_service.list_tasks(page_size=500)
        if args.environments:
            wanted_envs = set(args.environments.split(","))
            tasks = [t for t in tasks if t.environment in wanted_envs]
        if args.tasks:
            wanted_tasks = set(args.tasks.split(","))
            tasks = [t for t in tasks if t.task_id in wanted_tasks]

    print(
        f"[{batch_id}] {len(models)} models x {len(tasks)} tasks = "
        f"{len(models) * len(tasks)} runs total"
    )

    manifest = {
        "batch_id": batch_id,
        "started_at": datetime.now(UTC).isoformat(),
        "judge_provider": base_settings.judge_provider,
        "judge_model": base_settings.judge_model,
        "models": [
            {"label": m["label"], "provider": m["provider"], "model": m["model"]} for m in models
        ],
        "tasks": [t.task_id for t in tasks],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for model_cfg in models:
        label = model_cfg["label"]
        model_settings = resolve_model_settings(base_settings, model_cfg)
        skip_rest_of_model = False

        for task in tasks:
            if skip_rest_of_model:
                append_csv_row(
                    results_csv,
                    error_row(
                        batch_id=batch_id,
                        model_label=label,
                        model_cfg=model_cfg,
                        task_id=task.task_id,
                        environment=task.environment,
                        difficulty=task.difficulty,
                        attack_type=task.attack_type,
                        stage="skipped",
                        exc=RuntimeError("skipped after earlier config error"),
                    ),
                )
                continue

            if (label, task.task_id) in completed:
                continue

            print(f"[{batch_id}] {label} :: {task.task_id} ...", end=" ", flush=True)
            start = time.monotonic()
            try:
                row = await run_one(
                    database=database,
                    batch_id=batch_id,
                    output_dir=output_dir,
                    model_label=label,
                    model_cfg=model_cfg,
                    model_settings=model_settings,
                    task_id=task.task_id,
                    environment=task.environment,
                    difficulty=task.difficulty,
                    attack_type=task.attack_type,
                )
                append_csv_row(results_csv, row)
                append_jsonl_row(results_jsonl, row)
                print(
                    f"cts_raw={row['cts_raw']:.1f} cts_reported={row['cts_reported']:.1f} "
                    f"({row['trust_level']}) [{time.monotonic() - start:.1f}s]"
                )
            except CONFIG_FATAL_EXCEPTIONS as exc:
                # A config-shaped failure (bad key, unknown provider, missing task) almost
                # certainly means every remaining task for this model will fail the same way --
                # stop burning API calls on it. Narrower than "any AgentAuditError": a transient
                # rate limit or a one-off malformed request on a later conversation turn is NOT
                # config-shaped and must not cascade into skipping the rest of the model's tasks.
                print(f"CONFIG ERROR: {exc}")
                traceback.print_exc()
                append_csv_row(
                    results_csv,
                    error_row(
                        batch_id=batch_id,
                        model_label=label,
                        model_cfg=model_cfg,
                        task_id=task.task_id,
                        environment=task.environment,
                        difficulty=task.difficulty,
                        attack_type=task.attack_type,
                        stage="config",
                        exc=exc,
                    ),
                )
                skip_rest_of_model = True
            except AgentAuditError as exc:
                # Typed but transient/per-task (rate limit exhausted its retries, Judge JSON
                # hiccup, a malformed request from this task's own conversation state): record
                # it and move on to the next task for this model.
                print(f"ERROR: {exc}")
                traceback.print_exc()
                append_csv_row(
                    results_csv,
                    error_row(
                        batch_id=batch_id,
                        model_label=label,
                        model_cfg=model_cfg,
                        task_id=task.task_id,
                        environment=task.environment,
                        difficulty=task.difficulty,
                        attack_type=task.attack_type,
                        stage="run",
                        exc=exc,
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - one bad task must not abort the batch
                print(f"ERROR: {exc}")
                traceback.print_exc()
                append_csv_row(
                    results_csv,
                    error_row(
                        batch_id=batch_id,
                        model_label=label,
                        model_cfg=model_cfg,
                        task_id=task.task_id,
                        environment=task.environment,
                        difficulty=task.difficulty,
                        attack_type=task.attack_type,
                        stage="run",
                        exc=exc,
                    ),
                )

    await database.dispose()
    print(f"[{batch_id}] done. results: {results_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config", default="scripts/research_config.json", help="Path to the model list JSON."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to store results (default: research/results/<timestamp>).",
    )
    parser.add_argument(
        "--batch-id", default=None, help="Label for this batch; defaults to a UTC timestamp."
    )
    parser.add_argument(
        "--only-models", default=None, help="Comma-separated subset of model labels to run."
    )
    parser.add_argument("--tasks", default=None, help="Comma-separated subset of task_ids to run.")
    parser.add_argument(
        "--environments", default=None, help="Comma-separated subset of environments to run."
    )
    args = parser.parse_args()

    if args.output_dir is None:
        repo_root = BACKEND_ROOT.parent
        stamp = args.batch_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        args.output_dir = str(repo_root / "research" / "results" / stamp)

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
