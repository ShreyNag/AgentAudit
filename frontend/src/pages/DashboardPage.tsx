import { Activity, CheckCircle2, Clock, Gauge, ListChecks, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { statusTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonCard, SkeletonTable } from "@/components/ui/Skeleton";
import { StatCard } from "@/components/ui/StatCard";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/Table";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useProviderHealth } from "@/hooks/useProviders";
import { useRuns } from "@/hooks/useRuns";
import { formatDateTime, formatScore } from "@/lib/format";

/**
 * The application's landing page (PROJECT_SPEC_4 SS33-40): system status, recent activity,
 * execution metrics, and quick navigation.
 */
export default function DashboardPage() {
  const summary = useDashboardSummary();
  const recentRuns = useRuns({ page: 1, page_size: 5 });
  const providerHealth = useProviderHealth();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        <Link to="/benchmarks">
          <Button>Launch Benchmark</Button>
        </Link>
        <Link to="/analytics">
          <Button variant="secondary">View Analytics</Button>
        </Link>
      </div>

      {summary.isLoading && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}
      {summary.isError && <ErrorState error={summary.error} onRetry={() => summary.refetch()} />}
      {summary.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Total Runs" value={summary.data.total_runs} icon={ListChecks} />
          <StatCard
            label="Completed"
            value={summary.data.completed_runs}
            icon={CheckCircle2}
            tone="success"
          />
          <StatCard label="Failed" value={summary.data.failed_runs} icon={XCircle} tone="danger" />
          <StatCard label="Running" value={summary.data.running_runs} icon={Clock} tone="warning" />
        </div>
      )}
      {summary.data && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <StatCard
            label="Average CTS"
            value={
              summary.data.average_cts !== null ? formatScore(summary.data.average_cts) : "—"
            }
            icon={Gauge}
          />
          <StatCard
            label="Judge Connectivity"
            value={
              providerHealth.data
                ? providerHealth.data.judge.healthy
                  ? "Healthy"
                  : "Unreachable"
                : "Unknown"
            }
            icon={Activity}
            tone={providerHealth.data?.judge.healthy ? "success" : "warning"}
          />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
          <Link to="/runs" className="text-sm text-primary-600 hover:underline">
            View all
          </Link>
        </CardHeader>
        <CardContent>
          {recentRuns.isLoading && <SkeletonTable rows={3} />}
          {recentRuns.isError && (
            <ErrorState error={recentRuns.error} onRetry={() => recentRuns.refetch()} />
          )}
          {recentRuns.data && recentRuns.data.runs.length === 0 && (
            <EmptyState
              title="No runs yet"
              description="Launch a benchmark to see execution history here."
              action={
                <Link to="/benchmarks">
                  <Button size="sm">Launch Benchmark</Button>
                </Link>
              }
            />
          )}
          {recentRuns.data && recentRuns.data.runs.length > 0 && (
            <Table>
              <TableHead>
                <tr>
                  <TableHeaderCell>Run</TableHeaderCell>
                  <TableHeaderCell>Provider</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Created</TableHeaderCell>
                </tr>
              </TableHead>
              <TableBody>
                {recentRuns.data.runs.map((run) => (
                  <TableRow key={run.id} clickable>
                    <TableCell>
                      <Link to={`/runs/${run.id}`} className="text-primary-600 hover:underline">
                        {run.run_uuid.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell>
                      {run.provider} / {run.model}
                    </TableCell>
                    <TableCell>
                      <Badge tone={statusTone(run.status)}>{run.status}</Badge>
                    </TableCell>
                    <TableCell>{formatDateTime(run.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
