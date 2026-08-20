# AgentAudit

AgentAudit is a complete AI Agent Evaluation Framework that audits every stage of a tool-using
AI agent's execution — instruction, planning, memory, tool selection, tool invocation, tool
correctness, grounding, security, behaviour, and integrity — by analyzing the agent's complete
execution trace rather than only its final response.

Execution and evaluation are architecturally decoupled: AgentAudit records a benchmark run in
full, persists the trace, and only then evaluates it. Historical traces can be re-evaluated
without re-running the original agent.

This repository implements the specification defined in `PROJECT_SPEC_1.md` through
`PROJECT_SPEC_6.md` (see `prompt.txt` for the full source specification, and `docs/` for the
split, readable version plus architecture decision records).

## Repository Layout

```
backend/      FastAPI application: execution engine, evaluation engine, REST API, persistence
frontend/     React + TypeScript dashboard, trace viewer, evaluation reports, analytics
docker/       Dockerfiles for backend and frontend
docs/         Architecture guides, API reference, ADRs
scripts/      Developer utility scripts (seeding, migrations helpers)
examples/     Example agent implementations usable as an AUT
benchmarks/   Benchmark environment/task definitions consumed by the benchmark framework
tests/        Cross-cutting end-to-end scenario tests (see backend/tests for unit/integration)
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

This implementation was built in an environment with no Python, Node.js, Docker, or MySQL
installed, so nothing in this repository has actually been run: no `pip install`, no
`alembic upgrade`, no `pytest`, no `npm install`, no `npm run build`, no live LLM API call. Every
file was written to be correct by construction and cross-checked by hand against the
specification, but that is not a substitute for running it. Before trusting this in any real
capacity:

```bash
cd backend && pip install -e ".[dev]" && alembic upgrade head && pytest -q
cd frontend && npm install && npm run typecheck && npm run test -- --run && npm run build
docker compose up --build
```

Fix whatever those commands surface -- treat this codebase as a thorough first draft, not a
verified one.
