import { describe, expect, it } from "vitest";

import { describeEvent } from "@/features/trace/eventNarrative";
import type { TraceEvent } from "@/types/models";

function makeEvent(overrides: Partial<TraceEvent>): TraceEvent {
  return {
    event_number: 1,
    timestamp: "2026-08-19T00:00:00Z",
    event_type: "AgentStep",
    component: "external_agent",
    payload: {},
    latency: null,
    status: "ok",
    ...overrides,
  };
}

describe("describeEvent", () => {
  it("describes an AgentStep event recorded by AgentAuditTracer.record_event", () => {
    const event = makeEvent({
      payload: { input: { step_type: "memory_read", input: null }, output: { output: { hit: true } } },
    });
    const narrative = describeEvent(event);
    expect(narrative.headline).toBe("Agent step: memory_read.");
    expect(narrative.detail).toContain("hit");
  });

  it("omits detail when the AgentStep has no output", () => {
    const event = makeEvent({
      payload: { input: { step_type: "planning", input: null }, output: { output: null } },
    });
    expect(describeEvent(event).detail).toBeUndefined();
  });

  it("still falls back gracefully for a genuinely unknown event type", () => {
    const event = makeEvent({ event_type: "SomethingNew" });
    expect(describeEvent(event).headline).toBe("SomethingNew");
  });

  it("counts messages accurately for an AgentAudit-driven ProviderRequest (real messages array)", () => {
    const event = makeEvent({
      event_type: "ProviderRequest",
      component: "provider",
      payload: {
        input: {
          messages: [
            { role: "system", content: "You are a helpful assistant." },
            { role: "user", content: "What is the capital of Italy?" },
          ],
        },
        output: {},
      },
    });
    const narrative = describeEvent(event);
    expect(narrative.headline).toBe("Sent request to the model (2 message(s) in context).");
    expect(narrative.detail).toBeUndefined();
  });

  it("does not fabricate a message count for an external-agent ProviderRequest (raw string input)", () => {
    const event = makeEvent({
      event_type: "ProviderRequest",
      component: "external_agent",
      payload: {
        input: {
          input: "human: What is the capital of Italy?\nai: \nThe capital of Italy is Rome (Roma in Italian).\nhuman: What country is that city in?",
        },
        output: {},
      },
    });
    const narrative = describeEvent(event);
    expect(narrative.headline).not.toContain("0 message(s)");
    expect(narrative.headline).toBe("Sent request to the model (raw input recorded -- exact content below).");
    expect(narrative.detail).toBe(
      "human: What is the capital of Italy?\nai: \nThe capital of Italy is Rome (Roma in Italian).\nhuman: What country is that city in?",
    );
  });
});
