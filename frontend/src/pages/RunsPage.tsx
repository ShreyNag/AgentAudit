import { ListChecks } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { executionModeTone, statusTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonTable } from "@/components/ui/Skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/Table";
import { useRuns } from "@/hooks/useRuns";
import { formatDateTime, formatDuration } from "@/lib/format";

const STATUS_OPTIONS = ["", "queued", "running", "completed", "failed"];
const EXECUTION_MODE_OPTIONS = [
  { value: "", label: "All" },
  { value: "benchmark", label: "Benchmark" },
  { value: "external", label: "External" },
];

/** Run History (PROJECT_SPEC_4 SS47-49): search, filtering, sorting, pagination. Benchmark-driven
 * and externally observed runs share this one list -- filterable by Execution Mode rather than
 * split into separate pages, so a run's provenance is always visible, never hidden. */
export default function RunsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [provider, setProvider] = useState("");
  const [executionMode, setExecutionMode] = useState("");
  const pageSize = 20;

  const runs = useRuns({
    page,
    page_size: pageSize,
    status: status || undefined,
    provider: provider || undefined,
    execution_mode: executionMode || undefined,
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-wrap items-end gap-4 pt-5">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Status</label>
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setPage(1);
              }}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option === "" ? "All" : option}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Provider</label>
            <input
              value={provider}
              onChange={(event) => {
                setProvider(event.target.value);
                setPage(1);
              }}
              placeholder="e.g. anthropic"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Execution Mode</label>
            <select
              value={executionMode}
              onChange={(event) => {
                setExecutionMode(event.target.value);
                setPage(1);
              }}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            >
              {EXECUTION_MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {runs.isLoading && <SkeletonTable rows={6} />}
      {runs.isError && <ErrorState error={runs.error} onRetry={() => runs.refetch()} />}
      {runs.data && runs.data.runs.length === 0 && (
        <EmptyState icon={ListChecks} title="No runs found" description="Try adjusting your filters." />
      )}

      {runs.data && runs.data.runs.length > 0 && (
        <Card>
          <CardContent className="pt-5">
            <Table>
              <TableHead>
                <tr>
                  <TableHeaderCell>Run</TableHeaderCell>
                  <TableHeaderCell>Mode</TableHeaderCell>
                  <TableHeaderCell>Environment</TableHeaderCell>
                  <TableHeaderCell>Provider / Model</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Duration</TableHeaderCell>
                  <TableHeaderCell>Created</TableHeaderCell>
                </tr>
              </TableHead>
              <TableBody>
                {runs.data.runs.map((run) => (
                  <TableRow key={run.id} clickable>
                    <TableCell>
                      <Link to={`/runs/${run.id}`} className="text-primary-600 hover:underline">
                        {run.run_uuid.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge tone={executionModeTone(run.execution_mode)}>
                        {run.execution_mode}
                      </Badge>
                    </TableCell>
                    <TableCell>{run.environment}</TableCell>
                    <TableCell>
                      {run.provider} / {run.model}
                    </TableCell>
                    <TableCell>
                      <Badge tone={statusTone(run.status)}>{run.status}</Badge>
                    </TableCell>
                    <TableCell>{formatDuration(run.execution_time)}</TableCell>
                    <TableCell>{formatDateTime(run.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-gray-500">
                Page {page} of {runs.data.totalPages} ({runs.data.totalItems} runs)
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={page >= runs.data.totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
