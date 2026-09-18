# AgentAudit

AgentAudit is a complete AI Agent Evaluation Framework that audits every stage of a tool-using
AI agent's execution — instruction integrity, planner, memory, tool selection, tool invocation,
tool correctness, alignment, tool faithfulness, security, and execution integrity — by analyzing
the agent's complete execution trace rather than only its final response. Two further diagnostic
modules run on top of those ten scores: behavioural classification and failure attribution.

Execution and evaluation are architecturally decoupled: AgentAudit records a benchmark run in
full, persists the trace, and only then evaluates it. Historical traces can be re-evaluated
without re-running the original agent.

See `docs/` for the architecture guides, API reference, and architecture decision records.

## Repository Layout

```
backend/                     FastAPI application: execution engine, evaluation engine, REST API, persistence
  app/environments/          Benchmark environment/seed task definitions consumed by the benchmark framework
frontend/                    React + TypeScript dashboard, trace viewer, evaluation reports, analytics
docker/                      Dockerfiles for backend and frontend
docs/                        Architecture guides, API reference, ADRs
scripts/                     Developer utility scripts (seeding, migrations helpers)
examples/                    Example agent implementations usable as an AUT
tests/                       Cross-cutting end-to-end scenario tests (see backend/tests for unit/integration)
```

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- MySQL 8+ (primary datastore) -- or nothing at all for local dev, since `DATABASE_URL` can
  point at SQLite instead (see `.env.example`)
- Docker + Docker Compose (optional, only needed for the containerized quick start)

## Installation & Quick Start (Backend)

All backend dependencies (runtime + dev/test/lint/type-check) are declared in
`backend/pyproject.toml` -- there is no separate `requirements.txt`, by design (see
"Dependency Manifests" below).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"        # installs runtime + dev/test/lint/type-check dependencies

cp ../.env.example ../.env     # then fill in AUT_API_KEY / JUDGE_API_KEY at minimum
alembic upgrade head           # creates the schema (MySQL, or SQLite if DATABASE_URL is set)
uvicorn app.main:app --reload
```

API docs are then available at `http://localhost:8000/docs`.

## Installation & Quick Start (Frontend)

All frontend dependencies are declared in `frontend/package.json`.

```bash
cd frontend
npm install
cp .env.example .env            # point VITE_API_BASE_URL at your running backend if not default
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies `/api` to `http://localhost:8000`
(see `frontend/vite.config.ts`).

## Quick Start (Docker)

```bash
cp .env.example .env   # fill in AUT_API_KEY / JUDGE_API_KEY at minimum
docker compose up --build
```

## Testing

```bash
cd backend && pytest -q                                   # unit + integration tests
cd frontend && npm run typecheck && npm run test -- --run  # type-check + vitest
pytest -q                                                   # from repo root: full e2e lifecycle test
```

## Dependency Manifests

| Location | Purpose |
|---|---|
| `backend/pyproject.toml` | Backend runtime deps (`[project.dependencies]`) and dev/test/lint/type-check deps (`[project.optional-dependencies.dev]`), installed together via `pip install -e ".[dev]"`. Chosen over `requirements.txt` since this is a proper installable package (`setuptools`-built), not a script directory. |
| `frontend/package.json` | Frontend runtime `dependencies` and tooling `devDependencies`, plus the `dev`/`build`/`preview`/`test`/`lint`/`typecheck` scripts. |

Every entry in both manifests was derived by grepping the actual `import`/`from` statements
across `backend/app`, `backend/alembic`, `backend/tests`, `tests/`, and `frontend/src` -- not
guessed from the spec. A few dependencies are required despite never appearing in a literal
`import` statement in this codebase, because another library we do import needs them at runtime;
each is annotated inline in `backend/pyproject.toml`:

- `aiomysql` / `aiosqlite` -- loaded dynamically by SQLAlchemy based on the `mysql+aiomysql://` /
  `sqlite+aiosqlite://` DSN scheme in `DATABASE_URL`, never imported by name in our code.
- `python-dotenv` -- used internally by `pydantic-settings` because `Settings.model_config` sets
  `env_file=(...)`.
- `starlette` -- imported directly in `app/middleware/*.py` (not just re-exported through
  `fastapi`), so it's declared explicitly rather than relied on as a transitive dependency.

## Evaluating an Independently Running LLM Agent

AgentAudit can also evaluate an agent it does not execute: a chatbot, RAG pipeline, coding agent,
or any LangGraph/CrewAI/AutoGen/OpenAI-Agents-SDK/custom agent running in its own process. The
agent reports its LLM calls and tool calls to `AgentAuditTracer`
(`backend/app/trace/tracer.py`), which assembles the same `ExecutionTrace` the built-in execution
engine produces -- so the existing Evaluation Engine consumes either one unmodified. Runs created
this way are tagged `execution_mode: "external"` (vs `"benchmark"`) everywhere in the API/UI, and
are never mixed together in a way that implies AgentAudit drove them.

Try it from the frontend: **Independent Agents** in the sidebar
(`http://localhost:5173/independent-agents`) generates a run ID and copy-pasteable Python/curl
integration instructions, then shows the run in the normal Runs list (filterable by Execution
Mode) once your agent submits its trace. The page also shows the exact command for the bundled,
deterministic demo agent (no API key needed) as a clearly labeled "Development Demo," if you'd
rather verify the pipeline before wiring up a real agent:
`python -m examples.external_agent.independent_agent` from `backend/` (see
`examples/external_agent/README.md`). Full guide: `docs/external-agent-tracing-guide.md`.

## Design Principles

1. Execution is never modified by evaluation; evaluation starts only after execution finishes.
2. Every evaluator receives only the persisted execution trace and runs independently.
3. The execution trace is the single source of truth for all evaluation.
4. The framework is agent-framework-agnostic (OpenAI Agents SDK, LangGraph, CrewAI, AutoGen,
   MCP agents, custom agents).
5. The framework is provider-agnostic: every LLM call passes through a common provider
   interface, configured entirely via environment variables.

See `docs/adr/` for decisions made where the specification was ambiguous or internally
inconsistent across documents, and `docs/architecture.md`, `docs/deployment.md`,
`docs/provider-integration-guide.md`, `docs/environment-authoring-guide.md`, and
`docs/evaluation-engine-guide.md` for the rest of the developer documentation.

## Verification status

Stated plainly, rather than as a blanket "tests pass" claim:

- **Frontend** (`npm run typecheck && npm run test -- --run`): run and passing (60 tests).
- **Backend** (`pytest -q`): run and passing (313 tests) as of the most recent change to this
  repository.
- **Docker Compose build** (`docker compose up --build`): run and passing.
- **The benchmark pipeline itself has been executed end-to-end against live provider APIs**: 45
  model x task runs (5 models x 9 benchmark tasks) were each executed, persisted, and evaluated
  through the real Evaluation Engine with a live Judge call -- none of it mocked. Results are
  published in the preprint (see Citation below); see "Reproducing the published results" below
  for the exact configuration and how the runs were produced.

To verify all of the above yourself:

```bash
cd backend && pip install -e ".[dev]" && alembic upgrade head && pytest -q
cd frontend && npm install && npm run typecheck && npm run test -- --run && npm run build
docker compose up --build
```

## Reproducing the published results

The 45 published runs used:

- **Models evaluated** (`backend/scripts/research_config.example.json`): `gpt-5` (openai),
  `claude-sonnet-5` (anthropic), `gemini-2.5-flash` (gemini), `sarvam-105b` (sarvam), and
  `llama-3.3-70b` (groq, `llama-3.3-70b-versatile`) -- 5 models x the 9 seeded benchmark tasks
  (`backend/app/environments/*/seed_task.py`) = 45 runs.
- **Judge model**: `claude-sonnet-5` (anthropic), chosen as the strongest/most reliable judge
  available for consistent, high-quality rubric-based scoring. The same Judge configuration is
  held constant across every model in the batch (`JUDGE_PROVIDER`/`JUDGE_MODEL` in `backend/.env`
  are deliberately not overridden per model in `run_benchmark_suite.py`), which is what makes the
  scores comparable across models in the first place. Note that `claude-sonnet-5` is also one of
  the 5 evaluated models, so that model's row was judged by itself -- a self-judging case worth
  weighing when reading its results, not a hidden one.
- **Single-trial-per-cell design**: each (model, task) pair was run exactly once -- there is no
  repeated-trial/multi-seed averaging within a cell. Per-cell scores are therefore single-sample
  point estimates, not means over repeated attempts, and variance across models reflects one draw
  per model rather than a sampled distribution.

The 45 runs were produced through the frontend, not the batch CLI script below: the Benchmark
Launcher always runs against whichever `AUT_PROVIDER`/`AUT_MODEL`/`AUT_API_KEY` is configured in
`backend/.env` (provider/model are deliberately not per-run selectable in the UI --
`LaunchBenchmarkDialog`). Reproducing that exact process means, for each of the 5 models: set
`AUT_PROVIDER`/`AUT_MODEL`/`AUT_API_KEY` in `backend/.env` and restart the backend, then in
**Benchmarks** click Launch on each of the 9 seeded tasks, then open each run and click
**Evaluate Run** -- 5 models x 9 tasks = 45 runs.

`backend/scripts/run_benchmark_suite.py` is a batch-mode equivalent that does the same
launch-then-evaluate sequence for every (model, task) pair from a single config file, without
manually relaunching the frontend per model -- useful for a faster re-run, though it is not how
the original 45 runs were produced:

```bash
cd backend
cp scripts/research_config.example.json scripts/research_config.json  # fill in your own API keys
python scripts/run_benchmark_suite.py --config scripts/research_config.json
python scripts/generate_report_figures.py --results-dir research/results/<batch_id>
```

`research_config.json` holds live API keys and is git-ignored -- never commit it.

## Citation

If you use AgentAudit in your research, please cite:

```bibtex
@article{agentaudit2026,
  title   = {AgentAudit: A Complete Evaluation Framework for Tool-Using AI Agents},
  author  = {TODO},
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026}
}
```

(arXiv ID is a placeholder until the paper is live.)