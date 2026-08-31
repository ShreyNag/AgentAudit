import type { TraceEvent } from "@/types/models";

export interface EventNarrative {
  headline: string;
  detail?: string;
}

interface ToolCallPayload {
  tool_name?: string;
  arguments?: Record<string, unknown>;
}

/** Turns one raw trace event into a plain-English headline + detail (PROJECT_SPEC_4 Part 3). */
export function describeEvent(event: TraceEvent): EventNarrative {
  const input = (event.payload?.input ?? {}) as Record<string, unknown>;
  const output = (event.payload?.output ?? {}) as Record<string, unknown>;
  const error = event.payload?.error as string | null | undefined;

  switch (event.event_type) {
    case "RunStarted":
      return { headline: "Run started." };

    case "ProviderRequest": {
      // AgentAudit-driven runs record a real ProviderRequest with a messages: list[...] field
      // (app.trace.recorder.TraceRecorder.record_provider_request), so this count is accurate.
      if (Array.isArray(input.messages)) {
        const messages = input.messages;
        return {
          headline: `Sent request to the model (${messages.length} message(s) in context).`,
        };
      }
      // Externally observed agents record whatever raw value they passed as their own input
      // (app.trace.recorder.TraceRecorder.record_llm_call's `input={"input": input}` -- often a
      // free-form string, as here). There is no reliable message/turn count to derive from an
      // arbitrary raw value, so this deliberately makes no numeric claim (previously showed "0
      // message(s)", implying no context was sent, which was never actually true -- it just
      // couldn't count a shape it didn't recognize). The exact recorded input is shown in full
      // below instead of being summarized into a number or a claim about its content.
      const rawInput = input.input;
      return {
        headline: "Sent request to the model (raw input recorded -- exact content below).",
        detail:
          typeof rawInput === "string"
            ? rawInput
            : rawInput !== undefined
              ? JSON.stringify(rawInput)
              : undefined,
      };
    }

    case "ProviderResponse": {
      const toolCalls = (output.tool_calls as ToolCallPayload[]) ?? [];
      if (toolCalls.length > 0) {
        const names = toolCalls.map((call) => call.tool_name).join(", ");
        return { headline: `Model requested ${toolCalls.length} tool call(s): ${names}.` };
      }
      return { headline: "Model responded." };
    }

    case "ReasoningGenerated": {
      const available = Boolean(output.reasoning_available);
      const content = output.content as string | null;
      return available
        ? { headline: "Reasoning:", detail: content ?? undefined }
        : { headline: "No explicit reasoning was returned by the model for this turn." };
    }

    case "ToolSelected": {
      const name = (input.tool_name as string) ?? "unknown tool";
      const args = (input.arguments as Record<string, unknown>) ?? {};
      return {
        headline: `Model called tool "${name}".`,
        detail: Object.keys(args).length > 0 ? JSON.stringify(args) : undefined,
      };
    }

    case "ToolCompleted": {
      const name = (input.tool_name as string) ?? "tool";
      const result = output.output as Record<string, unknown> | undefined;
      return {
        headline: `Tool "${name}" completed successfully.`,
        detail: result && Object.keys(result).length > 0 ? JSON.stringify(result) : undefined,
      };
    }

    case "ToolFailed": {
      const name = (input.tool_name as string) ?? "tool";
      return {
        headline: `Tool "${name}" failed.`,
        detail: (output.error as string | undefined) ?? error ?? undefined,
      };
    }

    case "AgentStep": {
      const stepType = (input.step_type as string) ?? "step";
      const stepOutput = output.output;
      return {
        headline: `Agent step: ${stepType}.`,
        detail:
          stepOutput !== null && stepOutput !== undefined && stepOutput !== ""
            ? JSON.stringify(stepOutput)
            : undefined,
      };
    }

    case "Warning":
      return { headline: "Warning.", detail: error ?? undefined };

    case "Error":
      return { headline: "Error.", detail: error ?? undefined };

    case "RunCompleted":
      return { headline: "Run completed successfully." };

    case "RunFailed":
      return { headline: "Run failed.", detail: error ?? undefined };

    default:
      return { headline: event.event_type };
  }
}
