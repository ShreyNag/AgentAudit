# External Agent Example

`independent_agent.py` is a minimal LLM-based agent that runs entirely outside AgentAudit: its
own LLM, its own tools, its own execution loop. The only AgentAudit dependency in the agent's own
code is `AgentAuditTracer` (`backend/app/trace/tracer.py`). See
`docs/external-agent-tracing-guide.md` for the full guide, and the root `README.md` for how to
start AgentAudit itself (Docker or manual).

## Quick start (real HTTP, against a running backend)

This is the default -- what plain `python -m examples.external_agent.independent_agent` runs.
Start AgentAudit first (`docker compose up --build` from the repo root is the easiest way; the
backend listens on host port 8000 by default, or `${BACKEND_PORT}` if you've overridden it), then
**from the repository root** (`examples/` and `backend/` are siblings -- `python -m` needs that
layout, so this will *not* work from inside `backend/`):

```bash
backend/.venv/bin/python -m examples.external_agent.independent_agent
# or, if you've activated backend/.venv yourself: python -m examples.external_agent.independent_agent
```

No API key required. With no `AUT_API_KEY` set, the agent's own LLM calls use a deterministic
mock (`_MockLLM`) -- free, repeatable, and clearly printed as `Mode: MOCK`. The agent still runs
its full loop, calls its own tools, and submits a real trace over HTTP to
`POST /api/v1/runs/external`, so this exercises the entire tracing -> ingestion -> persistence
pipeline (and the frontend, if you open `http://localhost:5173/runs` afterwards) without spending
any API credits.

Expected output:

```
Mode: MOCK (no AUT_API_KEY set -- no LLM API key needed or used)
Run ID: <uuid> (id=<n>)
Agent: independent-trip-agent
Model: mock-llm-1
Trace event count: 36
Tool calls: calendar_lookup, flight_search, book_flight, book_flight, hotel_search, book_hotel, make_payment, make_payment
Final answer: Booked flight fl-2 ($480.00) and hotel htl-2 ($135.00) for 2026-08-13, and paid for both.
Composite Trust Score: 85.00
Trust level: High Trust
```

The last two lines only print if the AgentAudit backend has a real `JUDGE_API_KEY` configured
(evaluation always goes through the real Judge -- MOCK mode only covers the *agent's own* LLM
calls, never the server-side evaluation step). Without one, the script still reports success and
tells you exactly why evaluation didn't run:

```
Evaluation was not run (Server error '500 Internal Server Error' ...). The trace was still
successfully ingested as run <n> -- open it in the AgentAudit UI, or evaluate it later once a
Judge provider is configured (JUDGE_API_KEY in the backend's environment).
```

### Environment variables

All optional -- every one has a working default:

| Variable | Default | Purpose |
|---|---|---|
| `AGENTAUDIT_BASE_URL` | `http://localhost:8000` | The running AgentAudit backend to submit to. |
| `AGENTAUDIT_RUN_ID` | a generated UUID4 | Use a specific run_id (e.g. one already shown in the frontend's "Create External Run" panel). |
| `AGENTAUDIT_TASK_ID` | `trip_planner-001` | Set to `""` (empty) to run with no fixed ground truth. |
| `AGENTAUDIT_AGENT_NAME` | `independent-trip-agent` | Shown in the AgentAudit UI as the observed agent's name. |
| `AUT_PROVIDER` / `AUT_MODEL` / `AUT_API_KEY` / `AUT_BASE_URL` | unset (MOCK mode) | Set all three of `AUT_PROVIDER`/`AUT_MODEL`/`AUT_API_KEY` to make the agent's own LLM calls through a real provider (LIVE mode) instead of the mock. Never hard-code a real key here -- export it in your shell. |

```bash
# All run from the repository root, same as above. Point at a specific run_id the frontend
# already generated:
AGENTAUDIT_RUN_ID=abc-123 backend/.venv/bin/python -m examples.external_agent.independent_agent

# LIVE mode: the agent's own reasoning comes from a real model (tool logic stays deterministic,
# so the ground-truth comparison is unaffected):
AUT_PROVIDER=anthropic AUT_MODEL=claude-sonnet-5 AUT_API_KEY=sk-... \
  backend/.venv/bin/python -m examples.external_agent.independent_agent
```

## Fully offline demo (no server, no Docker, no key)

`AGENTAUDIT_MODE=embedded` runs the original self-contained variant: a temporary SQLite database
and a deterministic fake Judge, entirely in-process -- the fastest way to sanity-check the
tracing -> persistence -> evaluation pipeline in isolation:

```bash
# From the repository root, same layout requirement as above.
AGENTAUDIT_MODE=embedded backend/.venv/bin/python -m examples.external_agent.independent_agent
```

This is also what `backend/tests/test_external_agent_example.py` drives directly (via
`run_and_ingest`, against the real FastAPI test app) -- see it for the same flow exercised end to
end through the public REST API in a test.

## Raw HTTP, without the Python tracer

A genuinely separate agent (any language) can skip `AgentAuditTracer` entirely and POST a
pre-built trace directly:

```python
import httpx
from app.trace.tracer import AgentAuditTracer

tracer = AgentAuditTracer.start_run(
    task_id="trip_planner-001", environment="trip_planner", agent_name="my-agent",
)
# ... agent runs, calling tracer.record_llm_call() / tracer.record_tool_call() as it goes ...
trace = tracer.finish(final_output="Booked flight fl-2.", status="success")

response = httpx.post(
    "http://localhost:8000/api/v1/runs/external",
    json={
        "trace": trace.model_dump(mode="json"),
        "environment": "trip_planner",
        "provider": "openai",
        "model": "gpt-5",
        "task_id": "trip_planner-001",
    },
)
run_id = response.json()["data"]["id"]

# Trigger evaluation exactly like a benchmark-executed run:
httpx.post(f"http://localhost:8000/api/v1/runs/{run_id}/evaluate")
```

See `backend/tests/integration/api/test_external_traces.py` for this same flow driven end to end
against a real (test) FastAPI app, and the frontend's Independent Agents page
(`http://localhost:5173/independent-agents`) for the equivalent shown as copy-pasteable
instructions with a live "waiting for agent" status -- including this exact demo command,
pre-filled with a generated run_id, under "Run Local Demo Agent."
