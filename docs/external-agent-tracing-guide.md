# Evaluating an Independently Running LLM Agent

AgentAudit has two ways to get an `ExecutionTrace` in front of the Evaluation Engine.

**Execution mode** (the original path): AgentAudit drives the agent itself.
`POST /api/v1/benchmarks/run` resolves a benchmark task, calls the configured AUT provider,
invokes benchmark tools, and records every step through `TraceRecorder` as it happens
(`app/execution/common_agent_executor.py`).

**Observation mode** (this guide): an agent running entirely outside AgentAudit -- its own LLM
client, its own tools, its own loop, any framework or none -- reports what it did to
`AgentAuditTracer` (`app/trace/tracer.py`). The tracer assembles the exact same `ExecutionTrace`
type the execution engine produces. From that point on, ingestion, persistence, and evaluation are
identical: the Evaluation Engine has no idea which path a given run came from.

```
Execution mode                          Observation mode
───────────────                         ────────────────
Benchmark task                          Independently running agent
      │                                 (its own LLM, tools, loop, framework)
      ▼                                        │
CommonAgentExecutor                            ▼
      │                                 AgentAuditTracer
      │  TraceRecorder.record_*()              │  tracer.record_llm_call() /
      │  (internal engine API)                 │  record_tool_call() / trace_tool()
      ▼                                        ▼
      └──────────────► ExecutionTrace ◄────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
      ExecutionService.launch()   TraceIngestionService.ingest()
      (persists in-process)       (in-process, or via POST /api/v1/runs/external)
                │                           │
                └─────────────┬─────────────┘
                               ▼
                 persist_trace_artifacts()   <- one shared persistence path
                               │
                               ▼
                POST /api/v1/runs/{id}/evaluate
                               │
                               ▼
                   Evaluation Engine (unmodified)
                               │
                               ▼
                     Scores / CTS / Behaviour
```

## Why the evaluator needed no changes

`EvaluationContext` (`app/evaluation/context.py`) is built from the persisted `Run` +
`BenchmarkTask` rows and an `ExecutionTrace`. Every evaluator, the `BehaviourClassifier`, and the
`CTSCalculator` read only fields that both execution paths populate the same way: `messages`,
`tool_calls`/`tool_outputs`, `reasoning`/`reasoning_steps`, `errors`, `final_response`, `events`.
Fields only the internal engine ever fills (`trace.task`, `trace.memory`,
`trace.environment_changes`, `trace.observations`) are either unused by evaluators or, where used
(`evidence_extractor.py`'s `environment_changes`), simply empty for an observed run -- absence of
evidence, not a different schema. See `backend/tests/integration/services/
test_trace_ingestion_service.py::test_ingested_external_trace_is_evaluable_by_the_unmodified_evaluation_engine`
for the executable proof.

## The tracing API

`app/trace/tracer.py`'s `AgentAuditTracer` is the developer-facing surface. It never calls an LLM
or a tool itself -- it only records events the host code reports.

```python
from app.trace.tracer import AgentAuditTracer

tracer = AgentAuditTracer.start_run(
    task_id="trip_planner-001",
    environment="trip_planner",
    agent_name="trip-planner-bot",   # optional: the agent's own name/identity
    agent_id="v2",                    # optional: a deployment/version tag, if you have one
)

tracer.record_llm_call(
    model="gpt-5", provider="openai",
    input=messages, output=response_text,
    latency=0.8, usage={"input_tokens": 120, "output_tokens": 40},
)

# Proposal and result together, when your code observes both at once:
tracer.record_tool_call(
    tool_name="flight_search", input={"destination": "Mumbai"},
    output={"flights": [...]},
)

# Or split, when the LLM's tool call and its execution happen at different points:
call_id = tracer.record_tool_proposed(tool_name="book_flight", input={"flight_id": "fl-2"})
tracer.record_tool_result(tool_name="book_flight", input={"flight_id": "fl-2"},
                           output={"status": "booked"}, call_id=call_id)

# Any other step your agent takes worth recording (planning, memory, retrieval, a sub-agent
# handoff) -- no dedicated event type required:
tracer.record_event(step_type="memory_read", name="recall_preferences", output={...})

trace = tracer.finish(final_output="Booked flight fl-2.", status="success")
```

`trace` is a real `app.trace.models.ExecutionTrace` -- the same type
`CommonAgentExecutor`/`TraceRecorder` produce.

### Tracing tool calls with a decorator

For tools that are plain Python callables (sync or async), `trace_tool` records the
propose/execute/result boundary automatically and re-raises the tool's own exceptions unchanged:

```python
@tracer.trace_tool()
def search_database(query: str) -> list[dict]:
    ...

results = search_database("mumbai hotels")  # traced transparently
```

### Error handling: `strict` vs `best_effort`

`AgentAuditTracer(..., mode="best_effort")` (the default) logs and swallows a recording failure
rather than raising -- a bug in tracing must never take down the agent it's observing in
production. `mode="strict"` re-raises instead, for tests/CI where a broken tracer call should fail
loudly. The wrapped tool's own exceptions are never affected by `mode`; only the *recording* of
that exception is.

## Submitting a trace

**In-process** (same Python process/DB session as AgentAudit, e.g. a test or a script): call
`TraceIngestionService.ingest(trace=...)` directly -- see `examples/external_agent/
independent_agent.py::run_and_ingest`.

**Out-of-process** (a genuinely separate agent process/service): `POST /api/v1/runs/external`
with the serialized trace:

```bash
curl -X POST http://localhost:8000/api/v1/runs/external \
  -H "Content-Type: application/json" \
  -d '{
    "trace": '"$(python -c 'print(trace.model_dump_json())')"',
    "environment": "trip_planner",
    "provider": "openai",
    "model": "gpt-5",
    "task_id": "trip_planner-001"
  }'
```

Both paths are idempotent on `trace.run_uuid`: resubmitting returns the already-persisted run
rather than creating a duplicate. Both return a normal `RunModel`, ready for
`POST /api/v1/runs/{id}/evaluate` exactly like a benchmark-executed run. Its `execution_mode`
field is always `"external"` for a run created this way (`"benchmark"` for one AgentAudit
executed itself) -- the one field that distinguishes the two everywhere in the API/UI without
inspecting the trace itself.

### Checking whether AgentAudit has received your trace yet

If you generate a `run_id` *before* your agent runs (so you can hand it to your agent ahead of
time), poll `GET /api/v1/runs/external/{run_uuid}` to find out once it's been ingested:

```bash
curl http://localhost:8000/api/v1/runs/external/<run_id>
```

Returns `404` until a trace with that `run_uuid` has actually been submitted -- AgentAudit never
creates a run row for a promise of a trace, only for one it has actually observed -- then the
normal run object once it has. This is exactly what the frontend's Independent Agents page polls
(see below).

### `task_id`: comparing against a real benchmark, or not

- Pass a `task_id` that matches an already-registered `benchmark_tasks.task_id` (e.g.
  `"trip_planner-001"`) to evaluate the external run against that task's real ground truth and
  expected tool sequence -- this is what makes an externally traced run directly comparable to an
  AgentAudit-executed run of the same task.
- Omit `task_id`, or pass one that isn't registered, and `TraceIngestionService` creates a
  placeholder task from `task_instruction`/`ground_truth` in the request. There is no invented
  ground truth beyond what you supply -- evaluators that need it will simply have less to work
  with, the same as any AgentAudit task with a thin ground truth definition.

## Example

`examples/external_agent/independent_agent.py` is a complete, independent trip-planning agent:
its own LLM (`_MockLLM` by default, or `_LiveLLM` wrapping a real provider when `AUT_API_KEY` is
set), its own tools (`_LocalTravelTools`, plain Python methods, not
`app.environments.trip_planner`), its own loop (`run_independent_trip_agent`). The only
AgentAudit import anywhere in the agent's own logic is `AgentAuditTracer`. It reproduces the
`trip_planner-001` ground truth so its result is directly comparable to an AgentAudit-executed
run of that same task.

Two ways to run it, both **from the repository root** (`examples/` and `backend/` are siblings --
`python -m examples...` requires that layout, so this will not work from inside `backend/`):

```bash
# Default: submits over real HTTP to a running AgentAudit backend (e.g. `docker compose up`).
# MOCK mode (default, no API key) unless AUT_API_KEY is set -- see examples/external_agent/README.md.
backend/.venv/bin/python -m examples.external_agent.independent_agent

# Fully in-process (temporary SQLite DB, deterministic fake Judge) -- no server, no Docker, no key.
AGENTAUDIT_MODE=embedded backend/.venv/bin/python -m examples.external_agent.independent_agent
```

See `backend/tests/test_external_agent_example.py` for the equivalent driven through the real
FastAPI app and public REST endpoints, and `examples/external_agent/README.md` for the full
environment-variable reference and MOCK-vs-LIVE mode details.

## Frontend: the Independent Agents page

`http://localhost:5173/independent-agents` (sidebar: "Independent Agents") gives this whole flow
a UI, in three parts:

1. **How It Works** -- a static explanation of the flow (`Your Independent Agent ->
   AgentAuditTracer -> External Trace API -> Evaluation Engine -> Trust Score`) and the
   AgentAudit-driven-vs-independent distinction. No data, no run.
2. **Test Independent Agent** -- a form (Agent Name required; Agent ID, Provider, Model, an
   "Agent Endpoint / Trace Source" free-text note, Task ID, Test Instructions, Ground Truth,
   Metadata all optional) that generates a `run_id` client-side and nothing else -- no run row
   exists in AgentAudit yet. "Agent Endpoint / Trace Source" and Provider/Model are informational
   only (pre-fill the generated snippets); they are never sent as `ExternalRunIngestRequest`
   fields, since the schema has no such fields.
3. **Two test modes**, side by side, both feeding the same shared status panel:
   - **Run Local Demo Agent** -- shows the exact `python -m
     examples.external_agent.independent_agent` command (pre-filled with the generated
     `run_id` via `AGENTAUDIT_RUN_ID`), clearly labeled **Development Demo**. There is
     deliberately no in-browser "run" button: a browser cannot safely execute an arbitrary local
     process, and `examples/` isn't even shipped inside the backend's Docker image (see
     `docker/backend.Dockerfile`), so a server-side runner would need to add that as new attack
     surface for a dev-only convenience -- not worth it. You run the command yourself.
   - **Connect External Agent** -- the same Python/curl `AgentAuditTracer` integration snippets
     described above, for a real independent agent.

   The status panel polls `GET /api/v1/runs/external/{run_uuid}` and only shows "Trace received"
   once a trace has actually arrived -- via either mode, since AgentAudit can't tell (or care)
   which one you used.

From there, "Open Run" goes to the same Run Details page a benchmark-driven run uses, with an
"AgentAudit did not drive this run" banner and an Execution Mode badge so the two are never
confused. Nothing is ever shown as a score/trust level unless it actually came back from
`GET /runs/{id}/cts` -- an unevaluated run reads "not evaluated yet," and a failed evaluation
shows the real backend error, never a fabricated result. The Runs page's Execution Mode filter
(All/Benchmark/External) and the Analytics page's execution-mode breakdown chart use the same
`execution_mode` field.

## Docker

No extra setup: `docker compose up --build` already runs the `execution_mode` migration and
serves `POST /api/v1/runs/external` and `GET /api/v1/runs/external/{run_uuid}` on the backend's
existing port (host `8000` by default -- overridable via `BACKEND_PORT` in `.env` if something
else on your machine already uses 8000, without changing the container's internal port); the
frontend's Independent Agents page is served on host `5173` exactly like every other page,
proxied to the backend the same way (`docker/nginx.conf`'s `/api/` -> `http://backend:8000/api/`,
unaffected by `BACKEND_PORT` since that only changes the *host*-side mapping, not the internal
Docker network backend/frontend already talk over). See the root `README.md` and
`examples/external_agent/README.md` for exact commands.

## Running the Judge against a local Ollama model

Evaluation (`POST /runs/{id}/evaluate`) works identically for a benchmark-driven or externally
observed run -- it only ever reads `JUDGE_PROVIDER`/`JUDGE_MODEL`/`JUDGE_BASE_URL` from settings,
same as any other provider. No `JUDGE_API_KEY` is required for Ollama specifically
(`OllamaProvider.requires_api_key = False`); set it to any non-empty placeholder (e.g. `ollama`)
if your `.env` layout expects one to always be present.

```bash
JUDGE_PROVIDER=ollama
JUDGE_MODEL=llama3.1:latest
JUDGE_API_KEY=ollama
JUDGE_BASE_URL=http://host.docker.internal:11434   # see the Docker networking note below
JUDGE_TIMEOUT=300                                   # local inference regularly exceeds the 60s default
```

**Docker networking**: if the backend runs via `docker compose` (not a bare `uvicorn` on your
host), `localhost` inside the container means the container itself, not your Mac where Ollama is
listening -- use `http://host.docker.internal:11434` instead. This project has no
provider-specific `OLLAMA_BASE_URL` variable; the existing generic `AUT_BASE_URL`/`JUDGE_BASE_URL`
mechanism already covers any provider's custom endpoint (self-hosted, proxied, or otherwise), so
that's the one to set depending on whether Ollama is the AUT or the Judge (or both, with
independent models -- the two are never required to match).

**Model naming**: Ollama treats a tag-less name (`llama3.1`) as implicitly `:latest`
(`llama3.1:latest`); `GET /api/tags` always returns the fully-tagged form. `JudgeService` never
substitutes a different model than configured -- whatever `JUDGE_MODEL` is set to is sent to
Ollama verbatim.

**Before evaluating, `evaluate_run()` checks Judge health first** (`OllamaProvider.health_check()`
via `GET /api/tags`) and fails immediately with one clear diagnostic if the server is unreachable
or the configured model isn't pulled -- rather than fanning out to all ten evaluators (each
independently retrying) only to have every one fail the same way several minutes later. Check it
yourself the same way:

```bash
docker exec <backend-container> python -c "
import httpx
r = httpx.get('http://host.docker.internal:11434/api/tags', timeout=5)
print([m['name'] for m in r.json()['models']])
"
```

**Error diagnostics**: every Ollama/provider failure is mapped to a specific
`app.providers.exceptions.ProviderError` subtype with an accurate message (never a raw, opaque
500) -- connection refused, the connection dropped mid-response (e.g. Ollama crashed or ran out
of memory while generating), a timeout, an HTTP error status, or (via `JudgeService`) invalid JSON
in the Judge's response. The full underlying exception and stack trace are always in the backend
logs (`docker compose logs backend`); the response body sent to the client never includes secrets
or internals, only the category and a safe, specific message.

## Limitations

- No scoring methodology changed. An externally traced run is scored by the exact same rubrics
  and Judge as any other run; this integration adds a second way to produce an `ExecutionTrace`,
  not a second evaluator.
- Without a matching `task_id`, there is no fixed ground truth to score precision/correctness
  against beyond whatever `ground_truth` you submit -- evaluators are not given a fabricated one.
- The tracer records only what the host agent chooses to report. It cannot observe an agent's
  internal state that the integration code never calls `tracer.record_*` for.
- MOCK mode (the example script's default) only makes the *agent's own* LLM calls free -- it does
  not provide a mock Judge. Evaluating an ingested trace still requires the AgentAudit backend
  itself to have a real `JUDGE_API_KEY` configured; without one, ingestion still succeeds but
  `POST /runs/{id}/evaluate` fails, which the example script reports clearly rather than crashing.
- No live-updating trace: a run is either not yet ingested (`GET /runs/external/{run_uuid}`
  404s) or fully ingested in one atomic submission. There is no partial/streaming trace state to
  observe mid-run.
