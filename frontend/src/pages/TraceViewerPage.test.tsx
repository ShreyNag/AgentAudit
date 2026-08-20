import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import TraceViewerPage from "@/pages/TraceViewerPage";
import type { Run, TraceEvent } from "@/types/models";

const getRun = vi.fn();
vi.mock("@/api/services/runs", () => ({
  runsService: { get: (...args: unknown[]) => getRun(...args) },
}));

const getTimeline = vi.fn();
vi.mock("@/api/services/trace", () => ({
  traceService: {
    getTimeline: (...args: unknown[]) => getTimeline(...args),
    exportJsonUrl: () => "http://localhost:8000/api/v1/runs/9/export/json",
  },
}));

const externalRun: Run = {
  id: 9,
  run_uuid: "c208b5c1-6464-43ed-b2ab-398bd6581577",
  benchmark_task_id: 15,
  provider: "ollama",
  model: "llama2",
  judge_provider: "ollama",
  judge_model: "llama3.1:latest",
  environment: "langgraph_ollama_chatbot",
  status: "completed",
  execution_mode: "external",
  execution_time: 4.9427,
  start_time: "2026-08-20T05:13:43",
  end_time: "2026-08-20T05:13:43",
  created_at: "2026-08-20T05:13:42",
};

// The exact event shapes AgentAuditTracer/TraceRecorder produce for an externally observed run
// (component="external_agent", output={} rather than the fuller shape a driven benchmark run's
// ProviderResponse carries) -- guards the regression this was written for: the trace view must
// render this shape without throwing, not just the AgentAudit-driven shape.
const externalAgentTimeline: TraceEvent[] = [
  {
    event_number: 1,
    timestamp: "2026-08-20T05:13:38",
    event_type: "RunStarted",
    component: "runner",
    payload: { error: null, input: {}, output: {} },
    latency: null,
    status: "ok",
  },
  {
    event_number: 2,
    timestamp: "2026-08-20T05:13:42",
    event_type: "ProviderRequest",
    component: "external_agent",
    payload: {
      error: null,
      input: { input: "human: What is the capital of Italy?" },
      output: {},
    },
    latency: null,
    status: "ok",
  },
  {
    event_number: 3,
    timestamp: "2026-08-20T05:13:42",
    event_type: "ProviderResponse",
    component: "external_agent",
    payload: {
      error: null,
      input: {},
      output: { usage: {}, output: "\nThe capital of Italy is Rome (Roma in Italian)." },
    },
    latency: null,
    status: "ok",
  },
  {
    event_number: 4,
    timestamp: "2026-08-20T05:13:42",
    event_type: "ReasoningGenerated",
    component: "external_agent",
    payload: { error: null, input: {}, output: { content: null, reasoning_available: false } },
    latency: null,
    status: "ok",
  },
  {
    event_number: 8,
    timestamp: "2026-08-20T05:13:43",
    event_type: "RunCompleted",
    component: "runner",
    payload: { error: null, input: {}, output: {} },
    latency: null,
    status: "completed",
  },
];

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/runs/9/trace"]}>
        <Routes>
          <Route path="/runs/:id/trace" element={<TraceViewerPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TraceViewerPage", () => {
  it("renders an externally-observed run's real event shapes without a blank page", async () => {
    getRun.mockResolvedValue(externalRun);
    getTimeline.mockResolvedValue(externalAgentTimeline);

    renderPage();

    expect(await screen.findByText(/Run c208b5c1/)).toBeInTheDocument();
    expect(screen.getByText("Execution Timeline")).toBeInTheDocument();
    // All 5 events actually rendered as timeline cards, not silently dropped.
    expect(screen.getAllByText(/RunStarted|ProviderRequest|ProviderResponse|ReasoningGenerated|RunCompleted/).length).toBeGreaterThanOrEqual(5);
  });

  it("shows a real empty state, not a blank page, when a run genuinely has no trace events", async () => {
    getRun.mockResolvedValue(externalRun);
    getTimeline.mockResolvedValue([]);

    renderPage();

    expect(
      await screen.findByText("No trace events were recorded for this run"),
    ).toBeInTheDocument();
  });

  it("shows a real error state, not a blank page, when the timeline fails to load", async () => {
    getRun.mockResolvedValue(externalRun);
    getTimeline.mockRejectedValue(new Error("boom"));

    renderPage();

    expect(await screen.findByText("Something went wrong.")).toBeInTheDocument();
  });

  it("shows a headline and Raw data for every external-agent event when selected in the Inspector", async () => {
    getRun.mockResolvedValue(externalRun);
    getTimeline.mockResolvedValue(externalAgentTimeline);

    renderPage();
    await screen.findByText(/Run c208b5c1/);

    expect(
      screen.getByText("Select an event to inspect it in detail."),
    ).toBeInTheDocument();

    const cards = await screen.findAllByRole("button", {
      name: /RunStarted|ProviderRequest|ProviderResponse|ReasoningGenerated|RunCompleted/,
    });
    expect(cards).toHaveLength(externalAgentTimeline.length);

    for (const card of cards) {
      fireEvent.click(card);
      // The "select an event" placeholder must be gone and the Raw data panel must always
      // be present, regardless of which component ("runner" vs "external_agent") or payload
      // shape the selected event has.
      expect(
        screen.queryByText("Select an event to inspect it in detail."),
      ).not.toBeInTheDocument();
      expect(screen.getByText("Raw data")).toBeInTheDocument();
    }
  });
});
