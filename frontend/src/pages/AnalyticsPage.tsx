import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Alert } from "@/components/ui/Alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { StatCard } from "@/components/ui/StatCard";
import {
  useDashboardSummary,
  useEnvironmentBreakdown,
  useEvaluatorStatistics,
  useProviderBreakdown,
} from "@/hooks/useDashboard";
import { formatScore, titleCase } from "@/lib/format";

/**
 * Analytics (PROJECT_SPEC_4 Part 4 SS110-118): aggregate insights across every execution.
 *
 * Time-bucketed historical trend charts (CTS-over-time, rolling averages) are not implemented in
 * this build -- the backend Dashboard Service (Phase 10) exposes point-in-time aggregates
 * (summary/provider/environment/evaluator breakdowns) but no timestamped bucketing endpoint yet,
 * so this page presents exactly what is available rather than fabricating trend data.
 */
export default function AnalyticsPage() {
  const summary = useDashboardSummary();
  const providerBreakdown = useProviderBreakdown();
  const environmentBreakdown = useEnvironmentBreakdown();
  const evaluatorStats = useEvaluatorStatistics();

  return (
    <div className="space-y-6">
      <Alert
        tone="info"
        title="Historical trend charts are not yet available"
        description="The backend currently exposes point-in-time aggregates only; time-bucketed CTS trends would require an additional analytics endpoint."
      />

      {summary.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Total Runs" value={summary.data.total_runs} />
          <StatCard
            label="Average CTS"
            value={summary.data.average_cts !== null ? formatScore(summary.data.average_cts) : "—"}
          />
          <StatCard label="Completed" value={summary.data.completed_runs} tone="success" />
          <StatCard label="Failed" value={summary.data.failed_runs} tone="danger" />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Provider Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            {providerBreakdown.isLoading && <SkeletonCard />}
            {providerBreakdown.isError && (
              <ErrorState error={providerBreakdown.error} onRetry={() => providerBreakdown.refetch()} />
            )}
            {providerBreakdown.data && providerBreakdown.data.length === 0 && (
              <EmptyState title="No analytics yet" description="Launch some runs first." />
            )}
            {providerBreakdown.data && providerBreakdown.data.length > 0 && (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={providerBreakdown.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Benchmark Environment Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            {environmentBreakdown.data && environmentBreakdown.data.length === 0 && (
              <EmptyState title="No analytics yet" />
            )}
            {environmentBreakdown.data && environmentBreakdown.data.length > 0 && (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={environmentBreakdown.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#16a34a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Evaluator Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {evaluatorStats.data && evaluatorStats.data.length === 0 && (
            <EmptyState title="No evaluations yet" description="Evaluate a run to see evaluator trends." />
          )}
          {evaluatorStats.data && evaluatorStats.data.length > 0 && (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={evaluatorStats.data.map((item) => ({
                  ...item,
                  label: titleCase(item.evaluator_name),
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={70} />
                <YAxis domain={[0, 10]} />
                <Tooltip />
                <Bar dataKey="average_score" fill="#d97706" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
