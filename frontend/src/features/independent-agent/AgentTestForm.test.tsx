import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { AgentTestForm } from "@/features/independent-agent/AgentTestForm";

vi.mock("@/api/services/providers", () => ({
  providersService: { list: vi.fn().mockResolvedValue(["openai", "anthropic"]) },
}));
vi.mock("@/api/services/benchmarks", () => ({
  benchmarksService: {
    list: vi.fn().mockResolvedValue([]),
    listEnvironments: vi.fn().mockResolvedValue([]),
  },
}));

function renderWithQueryClient(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("AgentTestForm", () => {
  it("renders every field from the spec, grouped into agent metadata vs task/evaluation context", () => {
    renderWithQueryClient(<AgentTestForm onCreate={vi.fn()} />);
    expect(screen.getByText("Agent metadata")).toBeInTheDocument();
    expect(screen.getByText("Task / evaluation context")).toBeInTheDocument();
    expect(screen.getByText("Agent Name")).toBeInTheDocument();
    expect(screen.getByText("Agent ID (optional)")).toBeInTheDocument();
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText(/Agent Endpoint \/ Trace Source/)).toBeInTheDocument();
    expect(screen.getByText("Task ID (optional)")).toBeInTheDocument();
    expect(screen.getByText(/Test Instructions/)).toBeInTheDocument();
    expect(screen.getByText(/Ground Truth/)).toBeInTheDocument();
    expect(screen.getByText(/^Metadata/)).toBeInTheDocument();
  });

  it("requires an Agent Name before generating a run", () => {
    const onCreate = vi.fn();
    renderWithQueryClient(<AgentTestForm onCreate={onCreate} />);
    fireEvent.click(screen.getByRole("button", { name: /Generate Run ID/ }));
    expect(screen.getByText("Agent Name is required.")).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it("generates a run_id and calls onCreate once Agent Name is filled in", () => {
    const onCreate = vi.fn();
    renderWithQueryClient(<AgentTestForm onCreate={onCreate} />);
    fireEvent.change(screen.getByPlaceholderText("e.g. support-chatbot-v3"), {
      target: { value: "my-agent" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Generate Run ID/ }));

    expect(onCreate).toHaveBeenCalledTimes(1);
    const [config] = onCreate.mock.calls[0];
    expect(config.agentName).toBe("my-agent");
    expect(typeof config.runId).toBe("string");
    expect(config.runId.length).toBeGreaterThan(0);
  });

  it("rejects invalid JSON in Ground Truth without calling onCreate", () => {
    const onCreate = vi.fn();
    renderWithQueryClient(<AgentTestForm onCreate={onCreate} />);
    fireEvent.change(screen.getByPlaceholderText("e.g. support-chatbot-v3"), {
      target: { value: "my-agent" },
    });
    fireEvent.change(screen.getByPlaceholderText('{"expected_outcome": "..."}'), {
      target: { value: "{not valid json" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Generate Run ID/ }));

    expect(screen.getByText(/Ground Truth must be valid JSON/)).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it("passes the Agent Endpoint / Trace Source note through to the generated config", () => {
    const onCreate = vi.fn();
    renderWithQueryClient(<AgentTestForm onCreate={onCreate} />);
    fireEvent.change(screen.getByPlaceholderText("e.g. support-chatbot-v3"), {
      target: { value: "my-agent" },
    });
    fireEvent.change(
      screen.getByPlaceholderText(/runs on my laptop \/ a Lambda function/),
      { target: { value: "runs in a cron job" } },
    );
    fireEvent.click(screen.getByRole("button", { name: /Generate Run ID/ }));

    const [config] = onCreate.mock.calls[0];
    expect(config.traceSource).toBe("runs in a cron job");
  });
});
