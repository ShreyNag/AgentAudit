import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import RunDetailsPage from "@/pages/RunDetailsPage";
import type { Run } from "@/types/models";

const getRun = vi.fn();
vi.mock("@/api/services/runs", () => ({
  runsService: { get: (...args: unknown[]) => getRun(...args) },
}));

vi.mock("@/api/services/trace", () => ({
  traceService: {
    getTrace: vi.fn().mockResolvedValue({
      run_id: 1,
      planner: {},
      reasoning: {},
      messages: [],
      metadata: {},
      statistics: {},
      version: "1.0",
      created_at: "2026-08-19T00:00:00Z",
    }),
  },
}));

const getCts = vi.fn();
const evaluate = vi.fn();
vi.mock("@/api/services/evaluation", () => ({
  evaluationService: {
    getCts: (...args: unknown[]) => getCts(...args),
    getBehaviour: vi.fn().mockRejectedValue(new Error("not evaluated")),
    getFailure: vi.fn().mockResolvedValue(null),
    evaluate: (...args: unknown[]) => evaluate(...args),
  },
}));

function baseRun(overrides: Partial<Run> = {}): Run {
  return {
    id: 1,
    run_uuid: "run-abc-123",
    benchmark_task_id: 1,
    provider: "ollama",
    model: "llama2",
    judge_provider: null,
    judge_model: null,
    environment: "langgraph_ollama_chatbot",
    status: "completed",
    execution_mode: "external",
    execution_time: 12.5,
    start_time: "2026-08-19T00:00:00Z",
    end_time: "2026-08-19T00:00:12Z",
    created_at: "2026-08-19T00:00:00Z",
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/runs/1"]}>
        <Routes>
          <Route path="/runs/:id" element={<RunDetailsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RunDetailsPage Judge field", () => {
  it("shows -- / -- when the run has not been evaluated yet (judge fields absent)", async () => {
    getRun.mockResolvedValue(baseRun({ judge_provider: null, judge_model: null }));
    getCts.mockRejectedValue(new Error("not evaluated"));

    renderPage();

    expect(await screen.findByText("Judge")).toBeInTheDocument();
    expect(screen.getByText("— / —")).toBeInTheDocument();
  });

  it("shows the actual configured judge once the run has been evaluated", async () => {
    getRun.mockResolvedValue(
      baseRun({ judge_provider: "ollama", judge_model: "llama3.1:latest" }),
    );
    getCts.mockResolvedValue({ run_id: 1, cts: 30.0, trust_level: "Low Trust" });

    renderPage();

    expect(await screen.findByText("ollama / llama3.1:latest")).toBeInTheDocument();
  });

  it("never hardcodes ollama/llama3.1 -- displays whatever judge the API actually returns", async () => {
    // Agent provider/model deliberately non-ollama here too, so a stray "ollama" match could
    // only come from a hardcoded Judge value, never from an unrelated field on the page.
    getRun.mockResolvedValue(
      baseRun({
        provider: "anthropic",
        model: "claude-sonnet-5",
        judge_provider: "openai",
        judge_model: "gpt-5",
      }),
    );
    getCts.mockResolvedValue({ run_id: 1, cts: 85.0, trust_level: "High Trust" });

    renderPage();

    expect(await screen.findByText("openai / gpt-5")).toBeInTheDocument();
    expect(screen.queryByText(/ollama/)).not.toBeInTheDocument();
  });

  it("does not affect a benchmark-driven (non-external) run's display", async () => {
    getRun.mockResolvedValue(
      baseRun({
        execution_mode: "benchmark",
        judge_provider: "anthropic",
        judge_model: "claude-sonnet-5",
      }),
    );
    getCts.mockResolvedValue({ run_id: 1, cts: 90.0, trust_level: "High Trust" });

    renderPage();

    expect(await screen.findByText("anthropic / claude-sonnet-5")).toBeInTheDocument();
    // The "AgentAudit did not drive this run" banner is external-only.
    expect(screen.queryByText("AgentAudit did not drive this run.")).not.toBeInTheDocument();
  });

  it("updates the Judge field after clicking Evaluate Run, without a page reload", async () => {
    // Reproduces the exact reported bug: EvaluationService.evaluate_run() writes
    // judge_provider/judge_model onto the run row as a side effect of evaluating, but if
    // useEvaluateRun()'s onSuccess handler doesn't also invalidate the ["run", runId] query
    // (the one useRun/this page's Judge field reads from), the field keeps showing its
    // pre-evaluation value "-- / --" indefinitely, even though CTS/scores update correctly.
    getRun
      .mockResolvedValueOnce(baseRun({ judge_provider: null, judge_model: null }))
      .mockResolvedValueOnce(
        baseRun({ judge_provider: "ollama", judge_model: "llama3.1:latest" }),
      );
    getCts.mockRejectedValueOnce(new Error("not evaluated"));
    getCts.mockResolvedValueOnce({ run_id: 1, cts: 30.0, trust_level: "Low Trust" });
    evaluate.mockResolvedValue({
      run_id: 1,
      overall_reasoning: "",
      overall_summary: "",
      cts: 30.0,
      planner_summary: null,
      security_summary: null,
      integrity_summary: null,
      created_at: "2026-08-19T00:00:00Z",
    });

    renderPage();

    expect(await screen.findByText("— / —")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Evaluate Run" }));

    expect(await screen.findByText("ollama / llama3.1:latest")).toBeInTheDocument();
    expect(screen.queryByText("— / —")).not.toBeInTheDocument();
  });
});
