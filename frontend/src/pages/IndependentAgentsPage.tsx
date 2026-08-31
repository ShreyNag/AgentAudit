import { useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { AgentTestForm } from "@/features/independent-agent/AgentTestForm";
import { HowItWorks } from "@/features/independent-agent/HowItWorks";
import { IntegrationInstructions } from "@/features/independent-agent/IntegrationInstructions";
import { LocalDemoAgentPanel } from "@/features/independent-agent/LocalDemoAgentPanel";
import { WaitingForAgentPanel } from "@/features/independent-agent/WaitingForAgentPanel";
import type { AgentTestConfig } from "@/features/independent-agent/integrationSnippets";

/**
 * Independent Agents: test an LLM agent AgentAudit does not execute, only observes.
 *
 * "Generating a run" here only creates a run_id and integration instructions -- no run row
 * exists in AgentAudit, and nothing is contacted, until the independent agent itself submits a
 * trace to POST /api/v1/runs/external. Both test modes (Section 3) end at the same shared
 * status panel, since from AgentAudit's side a trace is a trace regardless of how it arrived.
 */
export default function IndependentAgentsPage() {
  const [activeRun, setActiveRun] = useState<AgentTestConfig | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Independent Agent Testing
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Evaluate an independently running LLM agent using AgentAudit tracing.
        </p>
      </div>

      {/* Section 1 -- How It Works */}
      <HowItWorks />

      <Alert
        tone="info"
        title="Task ID and ground truth"
        description={
          "Use a registered Task ID when you want the external run evaluated against a predefined benchmark task and ground truth. If no matching registered task exists, there is no fixed ground truth -- evaluators are never given a fabricated one."
        }
      />

      {/* Section 2 -- Test Independent Agent */}
      <Card>
        <CardHeader>
          <CardTitle>Test Independent Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <AgentTestForm onCreate={(config) => setActiveRun(config)} />
        </CardContent>
      </Card>

      {/* Section 3 -- Two test modes */}
      {activeRun && (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Run Local Demo Agent</CardTitle>
              </CardHeader>
              <CardContent>
                <LocalDemoAgentPanel config={activeRun} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Connect External Agent</CardTitle>
              </CardHeader>
              <CardContent>
                <IntegrationInstructions config={activeRun} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Run Status</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setActiveRun(null)}>
                Start a new test
              </Button>
            </CardHeader>
            <CardContent>
              <WaitingForAgentPanel runUuid={activeRun.runId} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
