/**
 * Builds the exact integration instructions shown on the Independent Agents page, from the real
 * backend surface only:
 *   - app.trace.tracer.AgentAuditTracer's actual constructor/method signatures
 *   - POST /api/v1/runs/external's actual request schema (app.schemas.external_trace.ExternalRunIngestRequest)
 *
 * Never fabricates the full ExecutionTrace JSON shape for the curl example -- that's assembled
 * by AgentAuditTracer itself, not something a user should hand-write.
 */

export interface AgentTestConfig {
  runId: string;
  agentName: string;
  agentId: string;
  provider: string;
  model: string;
  taskId: string;
  environment: string;
  /** Free-text note only -- where/how the agent runs and will submit its trace. Not a real
   * ExternalRunIngestRequest field, so it is never sent to the backend; it only appears as a
   * comment in the generated snippets, for the user's own reference. */
  traceSource: string;
}

/** The backend's own externally-reachable URL, independent of how this frontend itself talks to
 * the API (a Docker-proxied relative path like "/api/v1" is meaningless to an agent running
 * elsewhere) -- matches this project's Docker Compose port mapping (backend -> host 8000, or
 * ``${BACKEND_PORT}`` if overridden). */
export function defaultAgentAuditBaseUrl(hostname = "localhost", protocol = "http:"): string {
  return `${protocol}//${hostname}:8000/api/v1`;
}

export function buildIngestUrl(baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/runs/external`;
}

export function buildDemoCommand(config: AgentTestConfig, baseUrl: string): string {
  const { runId, taskId } = config;
  const backendBase = baseUrl.replace(/\/api\/v1\/?$/, "");
  // Must run from the repository root, NOT from backend/ -- `examples` and `backend` are
  // siblings, and `python -m examples...` resolves the `examples` package from the current
  // working directory, not from __file__. `backend/.venv/bin/python` works from any cwd without
  // needing the venv activated first (verified: this exact form of invocation was tested end to
  // end against a running backend before this snippet was written).
  const lines = [
    `AGENTAUDIT_RUN_ID=${runId} \\`,
    `AGENTAUDIT_BASE_URL=${backendBase} \\`,
  ];
  if (taskId) lines.push(`AGENTAUDIT_TASK_ID=${taskId} \\`);
  lines.push("backend/.venv/bin/python -m examples.external_agent.independent_agent");
  return lines.join("\n  ");
}

export function buildPythonSnippet(config: AgentTestConfig, baseUrl: string): string {
  const { runId, agentName, agentId, provider, model, taskId, environment, traceSource } = config;
  const sourceComment = traceSource ? `\n# Trace source: ${traceSource}` : "";
  return `# pip install httpx (or use your own HTTP client / see the curl example below)${sourceComment}
from app.trace.tracer import AgentAuditTracer

tracer = AgentAuditTracer.start_run(
    run_id="${runId}",
    task_id=${taskId ? `"${taskId}"` : "None"},
    agent_name="${agentName}",
    agent_id=${agentId ? `"${agentId}"` : "None"},
    environment="${environment}",
)

# ... your agent's own loop runs here, calling its own LLM/tools as usual ...

tracer.record_llm_call(
    model="${model || "your-model"}",
    provider="${provider || "your-provider"}",
    input="<prompt/messages your agent sent>",
    output="<the model's response>",
)

tracer.record_tool_call(
    tool_name="<tool your agent called>",
    input={"...": "..."},
    output={"...": "..."},
)

trace = tracer.finish(final_output="<the agent's final answer>", status="success")

# Submit over HTTP to this running AgentAudit backend:
import httpx
httpx.post(
    "${buildIngestUrl(baseUrl)}",
    json={
        "trace": trace.model_dump(mode="json"),
        "environment": "${environment}",
        "provider": "${provider || "your-provider"}",
        "model": "${model || "your-model"}",
        ${taskId ? `"task_id": "${taskId}",` : "// no task_id: evaluated without fixed ground truth"}
    },
)`;
}

export function buildCurlSnippet(config: AgentTestConfig, baseUrl: string): string {
  const { taskId, provider, model, environment } = config;
  return `curl -X POST "${buildIngestUrl(baseUrl)}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "trace": { /* build this with AgentAuditTracer.finish().model_dump(mode="json") --
                  see the Python example; do not hand-write an ExecutionTrace */ },
    "environment": "${environment}",
    "provider": "${provider || "your-provider"}",
    "model": "${model || "your-model"}"${taskId ? `,\n    "task_id": "${taskId}"` : ""}
  }'`;
}
