import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WaitingForAgentPanel } from "@/features/independent-agent/WaitingForAgentPanel";
import type { Run } from "@/types/models";

const getByUuid = vi.fn();
vi.mock("@/api/services/runs", () => ({
  runsService: { getByUuid: (...args: unknown[]) => getByUuid(...args) },
}));

function renderWithProviders(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

const RUN: Run = {
  id: 42,
  run_uuid: "run-abc-123",
  benchmark_task_id: 1,
  provider: "external-mock-llm",
  model: "mock-llm-1",
  judge_provider: null,
  judge_model: null,
  environment: "support_bot",
  status: "completed",
  execution_mode: "external",
  execution_time: 1.2,
  start_time: null,
  end_time: null,
  created_at: "2026-08-19T00:00:00Z",
};

describe("WaitingForAgentPanel", () => {
  it("shows a waiting state while no trace has been ingested yet (404 -> null)", async () => {
    getByUuid.mockResolvedValue(null);
    renderWithProviders(<WaitingForAgentPanel runUuid="run-abc-123" />);
    expect(await screen.findByText("Waiting for agent…")).toBeInTheDocument();
  });

  it("shows the received state with an Open Run link once ingested", async () => {
    getByUuid.mockResolvedValue(RUN);
    renderWithProviders(<WaitingForAgentPanel runUuid="run-abc-123" />);
    expect(await screen.findByText("Trace received.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Open Run" })).toHaveAttribute("href", "/runs/42");
    });
  });
});
