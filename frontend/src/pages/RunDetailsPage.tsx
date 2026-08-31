import React from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "@/api/client";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { behaviourTone, executionModeTone, statusTone, trustLevelTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { useBehaviour, useCts, useEvaluateRun, useFailure } from "@/hooks/useEvaluation";
import { useRun } from "@/hooks/useRuns";
import { useTrace } from "@/hooks/useTrace";
import { formatDateTime, formatDuration, formatPercent, formatScore, titleCase } from "@/lib/format";

/** Run Details (PROJECT_SPEC_4 SS50): summary, CTS, behaviour, failure attribution, links out.
 * Shared by both execution modes -- an externally observed run reads identically to a
 * benchmark-driven one, with an added banner and Execution Mode badge making the provenance
 * unmistakable (never implying AgentAudit drove a run it only observed). */
export default function RunDetailsPage() {
  const { id } = useParams();
  const runId = id ? Number(id) : undefined;

  const run = useRun(runId);
  const trace = useTrace(runId);
  const cts = useCts(runId);
  const behaviour = useBehaviour(runId);
  const failure = useFailure(runId);
  const evaluateRun = useEvaluateRun();

  if (run.isLoading) return <SkeletonCard />;
  if (run.isError || !run.data) return <ErrorState error={run.error} onRetry={() => run.refetch()} />;

  const data = run.data;
  const isExternal = data.execution_mode === "external";
  const agentName = trace.data?.metadata.agent_name as string | undefined;
  const agentId = trace.data?.metadata.agent_id as string | undefined;

  return (
    <div className="space-y-6">
      {isExternal && (
        <Alert
          tone="info"
          title="AgentAudit did not drive this run."
          description="This trace was produced by an independently running agent and only observed by AgentAudit -- see docs/external-agent-tracing-guide.md."
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Run {data.run_uuid}</CardTitle>
          <div className="flex gap-2">
            <Link to={`/runs/${data.id}/trace`}>
              <Button variant="secondary" size="sm">
                View Trace
              </Button>
            </Link>
            <Link to={`/runs/${data.id}/evaluation`}>
              <Button variant="secondary" size="sm">
                Evaluation Report
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Field label="Execution Mode">
            <Badge tone={executionModeTone(data.execution_mode)}>{data.execution_mode}</Badge>
          </Field>
          <Field label="Status">
            <Badge tone={statusTone(data.status)}>{data.status}</Badge>
          </Field>
          <Field label="Environment">{titleCase(data.environment)}</Field>
          <Field label="Provider / Model">
            {data.provider} / {data.model}
          </Field>
          {isExternal && (
            <>
              <Field label="Agent">{agentName ?? "—"}</Field>
              <Field label="Agent ID">{agentId ?? "—"}</Field>
            </>
          )}
          <Field label="Judge">
            {data.judge_provider ?? "—"} / {data.judge_model ?? "—"}
          </Field>
          <Field label="Duration">{formatDuration(data.execution_time)}</Field>
          <Field label="Started">{formatDateTime(data.start_time)}</Field>
          <Field label="Ended">{formatDateTime(data.end_time)}</Field>
          <Field label="Created">{formatDateTime(data.created_at)}</Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Composite Trust Score</CardTitle>
          {!cts.data && (
            <Button size="sm" loading={evaluateRun.isPending} onClick={() => evaluateRun.mutate(data.id)}>
              {evaluateRun.isPending ? "Evaluating…" : evaluateRun.isError ? "Retry Evaluation" : "Evaluate Run"}
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {cts.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
          {evaluateRun.isPending && (
            <p className="text-sm text-gray-500">
              Running all ten evaluators against the Judge model now. Against a local model (e.g.
              Ollama) this can take several minutes -- this page will update as soon as it finishes.
            </p>
          )}
          {!cts.isLoading && !cts.data && !evaluateRun.isPending && !evaluateRun.isError && (
            <p className="text-sm text-gray-500">
              This run has not been evaluated yet. Click "Evaluate Run" to generate a Composite
              Trust Score.
            </p>
          )}
          {!cts.isLoading && !cts.data && !evaluateRun.isPending && evaluateRun.isError && (
            <p className="text-sm text-danger-600">
              The last evaluation attempt failed:{" "}
              {evaluateRun.error instanceof ApiError ? evaluateRun.error.message : "Something went wrong."}
            </p>
          )}
          {cts.data && (
            <div className="flex items-center gap-6">
              <div>
                <p className="text-3xl font-bold">{formatScore(cts.data.cts)}</p>
                <p className="text-xs text-gray-500">out of 100</p>
              </div>
              <Badge tone={trustLevelTone(cts.data.trust_level)} className="text-sm">
                {cts.data.trust_level}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {behaviour.data && (
        <Card>
          <CardHeader>
            <CardTitle>Behaviour Classification</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Badge tone={behaviourTone(behaviour.data.classification)}>
              {titleCase(behaviour.data.classification)}
            </Badge>
            <p className="text-sm text-gray-600 dark:text-gray-300">{behaviour.data.reasoning}</p>
            <p className="text-xs text-gray-500">
              Confidence: {formatPercent(behaviour.data.confidence)}
            </p>
          </CardContent>
        </Card>
      )}

      {failure.data && (
        <Card>
          <CardHeader>
            <CardTitle>Failure Attribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm font-medium text-danger-600">
              Primary: {titleCase(failure.data.primary_failure)}
            </p>
            {failure.data.secondary_failures.length > 0 && (
              <p className="text-sm text-gray-500">
                Secondary: {failure.data.secondary_failures.map(titleCase).join(", ")}
              </p>
            )}
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {failure.data.diagnostic_reasoning}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-0.5 text-sm text-gray-900 dark:text-gray-100">{children}</p>
    </div>
  );
}
