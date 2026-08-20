import { describe, expect, it } from "vitest";

import {
  buildCurlSnippet,
  buildDemoCommand,
  buildIngestUrl,
  buildPythonSnippet,
  defaultAgentAuditBaseUrl,
  type AgentTestConfig,
} from "@/features/independent-agent/integrationSnippets";

const CONFIG: AgentTestConfig = {
  runId: "run-abc-123",
  agentName: "support-bot",
  agentId: "v2",
  provider: "openai",
  model: "gpt-5",
  taskId: "trip_planner-001",
  environment: "support_bot",
  traceSource: "runs on my laptop, submits over HTTP",
};

describe("defaultAgentAuditBaseUrl", () => {
  it("builds the backend's own externally-reachable URL, not a relative frontend proxy path", () => {
    expect(defaultAgentAuditBaseUrl("localhost", "http:")).toBe("http://localhost:8000/api/v1");
  });

  it("respects a custom hostname/protocol", () => {
    expect(defaultAgentAuditBaseUrl("192.168.1.5", "https:")).toBe(
      "https://192.168.1.5:8000/api/v1",
    );
  });
});

describe("buildIngestUrl", () => {
  it("matches the real POST /api/v1/runs/external endpoint path", () => {
    expect(buildIngestUrl("http://localhost:8000/api/v1")).toBe(
      "http://localhost:8000/api/v1/runs/external",
    );
  });

  it("tolerates a trailing slash on the base URL", () => {
    expect(buildIngestUrl("http://localhost:8000/api/v1/")).toBe(
      "http://localhost:8000/api/v1/runs/external",
    );
  });
});

describe("buildDemoCommand", () => {
  it("matches the real README-documented invocation, with the generated run_id wired in", () => {
    const command = buildDemoCommand(CONFIG, "http://localhost:8000/api/v1");
    expect(command).toContain("python -m examples.external_agent.independent_agent");
    expect(command).toContain("AGENTAUDIT_RUN_ID=run-abc-123");
    expect(command).toContain("AGENTAUDIT_BASE_URL=http://localhost:8000");
    expect(command).toContain("AGENTAUDIT_TASK_ID=trip_planner-001");
    // Must run from the repository root, not backend/ -- examples/ and backend/ are siblings,
    // so `cd backend` first would break `python -m examples...` (verified against a live
    // backend; this is not merely a stylistic preference).
    expect(command).not.toContain("cd backend");
    expect(command).toContain("backend/.venv/bin/python");
  });

  it("omits AGENTAUDIT_TASK_ID when no task id was given", () => {
    const command = buildDemoCommand({ ...CONFIG, taskId: "" }, "http://localhost:8000/api/v1");
    expect(command).not.toContain("AGENTAUDIT_TASK_ID");
  });
});

describe("buildPythonSnippet", () => {
  it("uses the real AgentAuditTracer.start_run/finish API and the config's run_id/task_id", () => {
    const snippet = buildPythonSnippet(CONFIG, "http://localhost:8000/api/v1");
    expect(snippet).toContain("AgentAuditTracer.start_run(");
    expect(snippet).toContain('run_id="run-abc-123"');
    expect(snippet).toContain('task_id="trip_planner-001"');
    expect(snippet).toContain('agent_name="support-bot"');
    expect(snippet).toContain('agent_id="v2"');
    expect(snippet).toContain("tracer.record_llm_call(");
    expect(snippet).toContain("tracer.record_tool_call(");
    expect(snippet).toContain("tracer.finish(");
    expect(snippet).toContain("http://localhost:8000/api/v1/runs/external");
  });

  it("passes task_id=None when no task id was given, rather than an empty string", () => {
    const snippet = buildPythonSnippet({ ...CONFIG, taskId: "" }, "http://localhost:8000/api/v1");
    expect(snippet).toContain("task_id=None");
  });
});

describe("buildCurlSnippet", () => {
  it("matches ExternalRunIngestRequest's real top-level fields without fabricating the trace body", () => {
    const snippet = buildCurlSnippet(CONFIG, "http://localhost:8000/api/v1");
    expect(snippet).toContain("POST");
    expect(snippet).toContain("http://localhost:8000/api/v1/runs/external");
    expect(snippet).toContain('"environment": "support_bot"');
    expect(snippet).toContain('"provider": "openai"');
    expect(snippet).toContain('"model": "gpt-5"');
    expect(snippet).toContain('"task_id": "trip_planner-001"');
    expect(snippet).not.toContain("run_uuid");
  });
});
