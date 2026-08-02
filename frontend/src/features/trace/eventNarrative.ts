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
      const messages = (input.messages as unknown[]) ?? [];
      return { headline: `Sent request to the model (${messages.length} message(s) in context).` };
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
