import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { CopyBlock } from "@/components/ui/CopyBlock";
import {
  buildDemoCommand,
  defaultAgentAuditBaseUrl,
  type AgentTestConfig,
} from "@/features/independent-agent/integrationSnippets";

/**
 * Mode A: "Run Local Demo Agent". Runs the actual, already-tested
 * examples/external_agent/independent_agent.py -- deterministic, no API key required -- to
 * verify the tracing -> ingestion -> evaluation pipeline end to end.
 *
 * There is deliberately no button here that executes anything: a browser cannot safely run an
 * arbitrary local Python process on your machine (and no backend "run this file" endpoint
 * exists either -- examples/ isn't even shipped inside the backend's Docker image, and adding a
 * command-execution endpoint reachable from the browser would be exactly the kind of
 * remote-code-execution surface this feature must not introduce). The command below is copied
 * verbatim from examples/external_agent/README.md; run it yourself, and this page's status
 * panel (shared with Mode B, below) detects it automatically once it submits its trace.
 */
export function LocalDemoAgentPanel({ config }: { config: AgentTestConfig }) {
  const baseUrl = defaultAgentAuditBaseUrl(window.location.hostname, window.location.protocol);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-md border border-warning-200 bg-warning-100/40 px-3 py-2 text-xs text-warning-700 dark:border-warning-600/30 dark:bg-warning-600/10 dark:text-warning-600">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span>
          <Badge tone="warning" className="mr-1.5 align-middle">
            Development Demo
          </Badge>
          Runs the bundled example agent from your own terminal -- deterministic, free, no API
          key. AgentAudit does not execute this for you; there is no in-browser "run" button by
          design (see the note in the code).
        </span>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-300">
        Run the included independent-agent example to verify that external tracing, ingestion,
        and evaluation work end-to-end.
      </p>

      <CopyBlock label="Run this from the repository root" text={buildDemoCommand(config, baseUrl)} />

      <p className="text-xs text-gray-500">
        This is exactly <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">
        python -m examples.external_agent.independent_agent</code> (see
        <code className="rounded bg-gray-100 px-1 dark:bg-gray-800"> examples/external_agent/README.md</code>),
        pre-filled with the Run ID above via <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">AGENTAUDIT_RUN_ID</code> so
        it reports back to this exact run. No result is shown here until it actually finishes and
        submits its trace -- the status panel below updates automatically.
      </p>
    </div>
  );
}
