import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { executionModeTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { useRunByUuid } from "@/hooks/useRuns";

const SLOW_HINT_AFTER_MS = 30_000;

/**
 * Polls GET /api/v1/runs/external/{run_uuid} until AgentAudit has observed a trace for this
 * run_id -- a 404 here is the normal "still waiting" state (see external_traces.py's
 * get_external_run_by_uuid), not an error. AgentAudit never fabricates a "receiving" progress
 * state for what is, underneath, one atomic HTTP POST; the only two real states are "not
 * ingested yet" and "ingested".
 */
export function WaitingForAgentPanel({ runUuid }: { runUuid: string }) {
  const query = useRunByUuid(runUuid, true);
  const [showSlowHint, setShowSlowHint] = useState(false);

  useEffect(() => {
    setShowSlowHint(false);
    const timer = setTimeout(() => setShowSlowHint(true), SLOW_HINT_AFTER_MS);
    return () => clearTimeout(timer);
  }, [runUuid]);

  if (query.data) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-success-100 bg-success-100/40 px-4 py-3 dark:border-success-600/30 dark:bg-success-600/10">
        <div>
          <p className="text-sm font-medium text-success-700 dark:text-success-600">
            Trace received.
          </p>
          <p className="mt-0.5 flex items-center gap-2 text-xs text-gray-500">
            Run <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{query.data.run_uuid.slice(0, 8)}</code>
            <Badge tone={executionModeTone(query.data.execution_mode)}>
              {query.data.execution_mode}
            </Badge>
            <Badge tone="neutral">{query.data.status}</Badge>
          </p>
        </div>
        <Link to={`/runs/${query.data.id}`}>
          <Button size="sm">Open Run</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-dashed border-gray-300 px-4 py-4 dark:border-gray-700">
      <div className="flex items-center gap-2">
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Waiting for agent…</p>
      </div>
      <p className="mt-1 text-xs text-gray-500">
        No trace has been received for this run yet. This page checks automatically every few
        seconds -- run your agent using the instructions above whenever you're ready.
      </p>
      {showSlowHint && (
        <p className="mt-2 text-xs text-warning-600">
          Still nothing after 30s. If your agent already ran, double-check it POSTed to the exact
          URL above with <code>run_id: "{runUuid}"</code>, and that it can reach this machine.
        </p>
      )}
    </div>
  );
}
