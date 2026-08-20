import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import IndependentAgentsPage from "@/pages/IndependentAgentsPage";

vi.mock("@/api/services/providers", () => ({
  providersService: { list: vi.fn().mockResolvedValue(["openai", "anthropic"]) },
}));
vi.mock("@/api/services/benchmarks", () => ({
  benchmarksService: {
    list: vi.fn().mockResolvedValue([]),
    listEnvironments: vi.fn().mockResolvedValue([]),
  },
}));
vi.mock("@/api/services/runs", () => ({
  runsService: { getByUuid: vi.fn().mockResolvedValue(null) },
}));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <IndependentAgentsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("IndependentAgentsPage", () => {
  it("renders the page title, subtitle, How It Works section, and the test form", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: "Independent Agent Testing" })).toBeInTheDocument();
    expect(
      screen.getByText("Evaluate an independently running LLM agent using AgentAudit tracing."),
    ).toBeInTheDocument();
    expect(screen.getByText("How It Works")).toBeInTheDocument();
    expect(screen.getByText("Your Independent Agent")).toBeInTheDocument();
    expect(screen.getByText("AgentAuditTracer")).toBeInTheDocument();
    expect(screen.getByText("Trust Score")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Test Independent Agent" })).toBeInTheDocument();
  });

  it("does not show the two test-mode cards or status panel before a run is generated", () => {
    renderPage();
    expect(screen.queryByText("Run Local Demo Agent")).not.toBeInTheDocument();
    expect(screen.queryByText("Connect External Agent")).not.toBeInTheDocument();
    expect(screen.queryByText("Run Status")).not.toBeInTheDocument();
  });

  it("shows both test modes and a shared status panel once a run is generated", async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText("e.g. support-chatbot-v3"), {
      target: { value: "my-agent" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Generate Run ID/ }));

    expect(await screen.findByText("Run Local Demo Agent")).toBeInTheDocument();
    expect(screen.getByText("Connect External Agent")).toBeInTheDocument();
    expect(screen.getByText("Development Demo")).toBeInTheDocument();
    expect(screen.getAllByText(/python -m examples.external_agent.independent_agent/).length).toBeGreaterThan(0);
    expect(screen.getByText(/AGENTAUDIT_RUN_ID=/)).toBeInTheDocument();
    expect(screen.getByText("http://localhost:8000/api/v1/runs/external")).toBeInTheDocument();
    expect(await screen.findByText("Waiting for agent…")).toBeInTheDocument();
  });
});
