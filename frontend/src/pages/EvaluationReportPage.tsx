import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/Badge";
import { behaviourTone, trustLevelTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EvaluatorCard } from "@/features/evaluation/EvaluatorCard";
import { ScoreRadarChart } from "@/features/evaluation/ScoreRadarChart";
import { TraceNarrativeList } from "@/features/trace/TraceNarrativeList";
import {
  useBehaviour,
  useCts,
  useEvaluateRun,
  useEvaluationScores,
  useFailure,
  useRubrics,
} from "@/hooks/useEvaluation";
import { useRun } from "@/hooks/useRuns";
import { useTimeline } from "@/hooks/useTrace";
import { formatPercent, formatScore, titleCase } from "@/lib/format";

/**
 * Evaluation Report (PROJECT_SPEC_4 Part 4): the single reviewer-facing page for one run, top to
 * bottom -- Composite Trust Score, behavioural verdict + why, the full execution cycle in plain
 * English, then every metric scored individually against its own rubric.
 */
export default function EvaluationReportPage() {
  const { id } = useParams();
  const runId = id ? Number(id) : undefined;
  const [traceExpanded, setTraceExpanded] = useState(true);

  const run = useRun(runId);
  const cts = useCts(runId);
  const scores = useEvaluationScores(runId);
  const behaviour = useBehaviour(runId);
  const failure = useFailure(runId);
  const rubrics = useRubrics();
  const timeline = useTimeline(runId);
  const evaluateRun = useEvaluateRun();

  if (run.isLoading) return <SkeletonCard />;
  if (run.isError || !run.data) return <ErrorState error={run.error} onRetry={() => run.refetch()} />;

  const recommendations = Array.from(
    new Set((scores.data ?? []).flatMap((score) => score.matched_criteria)),
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Evaluation Report</CardTitle>
            <p className="mt-0.5 text-xs text-gray-500">Run {run.data.run_uuid}</p>
          </div>
          <Link to={`/runs/${run.data.id}/trace`}>
            <Button variant="secondary" size="sm">
              Raw Trace / JSON
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {!cts.data && !cts.isLoading && (
            <EmptyState
              title={evaluateRun.isPending ? "Evaluating…" : "No evaluation available"}
              description={
                evaluateRun.isPending
                  ? "Running all ten evaluators against the Judge model now. Against a local model " +
                    "(e.g. Ollama) this can take several minutes -- this page will update as soon " +
                    "as it finishes."
                  : evaluateRun.isError
                    ? `The last evaluation attempt failed: ${
                        evaluateRun.error instanceof ApiError
                          ? evaluateRun.error.message
                          : "Something went wrong."
                      }`
                    : "This run has not been evaluated yet."
              }
              action={
                <Button loading={evaluateRun.isPending} onClick={() => evaluateRun.mutate(run.data.id)}>
                  {evaluateRun.isPending
                    ? "Evaluating…"
                    : evaluateRun.isError
                      ? "Retry Evaluation"
                      : "Evaluate Run"}
                </Button>
              }
            />
          )}
        </CardContent>
      </Card>

      {cts.data && (
        <>
          {/* 1. Composite Trust Score, front and center */}
          <Card>
            <CardContent className="flex flex-col items-center justify-center gap-1 pt-8 pb-8 text-center">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                Composite Trust Score
              </p>
              <p className="text-6xl font-bold text-gray-900 dark:text-gray-100">
                {formatScore(cts.data.cts_reported)}
              </p>
              <p className="text-xs text-gray-500">out of 100</p>
              <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
                <Badge tone={trustLevelTone(cts.data.trust_level)} className="text-sm">
                  {cts.data.trust_level}
                </Badge>
                {cts.data.critical_failure && (
                  <Badge tone="danger" className="text-sm">
                    Critical failure: {cts.data.critical_failure_modules.map(titleCase).join(", ")}
                  </Badge>
                )}
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Uncapped score: {formatScore(cts.data.cts_raw)} / 100
              </p>
            </CardContent>
          </Card>

          {/* 2. Behavioural classification + justification */}
          {behaviour.data && (
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Behavioural Analysis</CardTitle>
                  <p className="mt-0.5 text-xs text-gray-500">
                    How the agent behaved overall, and why this label fits better than the alternatives.
                  </p>
                </div>
                <Badge tone={behaviourTone(behaviour.data.classification)} className="text-sm">
                  {titleCase(behaviour.data.classification)}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm text-gray-600 dark:text-gray-300">{behaviour.data.reasoning}</p>
                <p className="text-xs text-gray-500">
                  Confidence: {formatPercent(behaviour.data.confidence)}
                </p>
                {behaviour.data.evidence.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                      Supporting Evidence
                    </p>
                    <ul className="ml-4 list-disc text-sm text-gray-600 dark:text-gray-300">
                      {behaviour.data.evidence.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
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

          {/* 3. The entire execution cycle, in plain English */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Execution Trace</CardTitle>
                <p className="mt-0.5 text-xs text-gray-500">
                  What the model decided at each step, which tool it called and how, and what came
                  back -- the full cycle, human-readable.
                </p>
              </div>
              <Button variant="secondary" size="sm" onClick={() => setTraceExpanded((prev) => !prev)}>
                {traceExpanded ? "Collapse" : "Expand"}
              </Button>
            </CardHeader>
            {traceExpanded && (
              <CardContent>
                {timeline.isLoading && <SkeletonCard />}
                {timeline.isError && (
                  <ErrorState error={timeline.error} onRetry={() => timeline.refetch()} />
                )}
                {timeline.data && <TraceNarrativeList events={timeline.data} />}
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Score Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {scores.data && scores.data.length > 0 && <ScoreRadarChart scores={scores.data} />}
            </CardContent>
          </Card>

          {/* 4. Every metric, individually, out of 100, with reasoning + rubric */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Evaluator Scores</CardTitle>
                <p className="mt-0.5 text-xs text-gray-500">
                  Each of the ten metrics, scored out of 100 against its own rubric -- expand any
                  card for the full reasoning and a criterion-by-criterion breakdown.
                </p>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {scores.data?.map((score) => (
                <EvaluatorCard
                  key={score.evaluator_name}
                  score={score}
                  rubric={rubrics.data?.[score.evaluator_name]}
                />
              ))}
            </CardContent>
          </Card>

          {recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="ml-4 list-disc space-y-1 text-sm text-gray-600 dark:text-gray-300">
                  {recommendations.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
