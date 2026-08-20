import { CopyBlock } from "@/components/ui/CopyBlock";
import {
  buildCurlSnippet,
  buildIngestUrl,
  buildPythonSnippet,
  defaultAgentAuditBaseUrl,
  type AgentTestConfig,
} from "@/features/independent-agent/integrationSnippets";

const STEPS = [
  "Create an AgentAuditTracer in your agent.",
  "Run your agent normally.",
  "Record model calls and tool calls.",
  "Submit the trace to AgentAudit.",
  "AgentAudit evaluates the run.",
];

/**
 * Mode B: "Connect External Agent". Everything an independent agent's own code needs to report
 * its execution to AgentAudit, generated from the real backend surface exactly:
 * app.trace.tracer.AgentAuditTracer and POST /api/v1/runs/external
 * (app.schemas.external_trace.ExternalRunIngestRequest) -- never invented.
 */
export function IntegrationInstructions({ config }: { config: AgentTestConfig }) {
  const baseUrl = defaultAgentAuditBaseUrl(window.location.hostname, window.location.protocol);

  return (
    <div className="space-y-4">
      <div>
        <p className="mb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
          Run your agent independently and send its AgentAudit trace to this application.
        </p>
        <ol className="list-inside list-decimal space-y-1 text-sm text-gray-600 dark:text-gray-300">
          {STEPS.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <CopyBlock label="Run ID" text={config.runId} />
        <CopyBlock label="External Trace API — POST" text={buildIngestUrl(baseUrl)} />
      </div>
      <p className="text-xs text-gray-500">
        If your agent runs on a different machine, replace{" "}
        <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{window.location.hostname}</code>{" "}
        with an address it can reach this AgentAudit backend at.
      </p>

      <CopyBlock label="Python (recommended -- uses AgentAuditTracer)" text={buildPythonSnippet(config, baseUrl)} />
      <CopyBlock label="Raw HTTP (any language)" text={buildCurlSnippet(config, baseUrl)} />
    </div>
  );
}
