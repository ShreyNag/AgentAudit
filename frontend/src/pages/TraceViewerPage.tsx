import React, { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { traceService } from "@/api/services/trace";
import { Badge } from "@/components/ui/Badge";
import { statusTone } from "@/components/ui/badgeTones";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { describeEvent } from "@/features/trace/eventNarrative";
import { TimelineEventCard } from "@/features/trace/TimelineEventCard";
import { useRun } from "@/hooks/useRuns";
import { useTimeline } from "@/hooks/useTrace";
import { formatDuration } from "@/lib/format";
import type { TraceEvent } from "@/types/models";

const ALL_TYPES = "all";

/**
 * Execution Trace Viewer (PROJECT_SPEC_4 Part 3). Read-only chronological inspection of every
 * planner decision, message, tool invocation, and environment update. Full play/pause replay
 * animation is out of scope for this build -- the timeline itself already presents the
 * persisted, immutably-ordered event sequence (PROJECT_SPEC_1 SS69/SS70), which is the
 * functional core of "replay" without needing a redundant animated player.
 */
export default function TraceViewerPage() {
  const { id } = useParams();
  const runId = id ? Number(id) : undefined;
  const [selectedEvent, setSelectedEvent] = useState<TraceEvent | null>(null);
  const [typeFilter, setTypeFilter] = useState(ALL_TYPES);
  const [search, setSearch] = useState("");

  const run = useRun(runId);
  const timeline = useTimeline(runId);

  const eventTypes = useMemo(
    () => Array.from(new Set((timeline.data ?? []).map((event) => event.event_type))),
    [timeline.data],
  );

  const filteredEvents = useMemo(() => {
    return (timeline.data ?? []).filter((event) => {
      if (typeFilter !== ALL_TYPES && event.event_type !== typeFilter) return false;
      if (search && !JSON.stringify(event).toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [timeline.data, typeFilter, search]);

  if (run.isLoading) return <SkeletonTable rows={6} />;
  if (run.isError || !run.data) return <ErrorState error={run.error} onRetry={() => run.refetch()} />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Run {run.data.run_uuid}</CardTitle>
          <div className="flex gap-2">
            <Link to={`/runs/${run.data.id}`}>
              <Button variant="secondary" size="sm">
                Run Summary
              </Button>
            </Link>
            <Link to={`/runs/${run.data.id}/evaluation`}>
              <Button variant="secondary" size="sm">
                Evaluation Report
              </Button>
            </Link>
            <a href={traceService.exportJsonUrl(run.data.id)} target="_blank" rel="noreferrer">
              <Button variant="secondary" size="sm">
                Export JSON
              </Button>
            </a>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6 text-sm">
          <Stat label="Status">
            <Badge tone={statusTone(run.data.status)}>{run.data.status}</Badge>
          </Stat>
          <Stat label="Duration">{formatDuration(run.data.execution_time)}</Stat>
          <Stat label="Events">{timeline.data?.length ?? "—"}</Stat>
          <Stat label="Provider">
            {run.data.provider} / {run.data.model}
          </Stat>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Execution Timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search events…"
                className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
              />
              <select
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
              >
                <option value={ALL_TYPES}>All types</option>
                {eventTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {timeline.isLoading && <SkeletonTable rows={5} />}
            {timeline.isError && (
              <ErrorState error={timeline.error} onRetry={() => timeline.refetch()} />
            )}
            {filteredEvents.length === 0 && !timeline.isLoading && (
              <EmptyState title="No matching events" description="Try clearing your filters." />
            )}
            <div className="max-h-[32rem] space-y-2 overflow-y-auto pr-1">
              {filteredEvents.map((event) => (
                <TimelineEventCard
                  key={event.event_number}
                  event={event}
                  selected={selectedEvent?.event_number === event.event_number}
                  onSelect={() => setSelectedEvent(event)}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inspector</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selectedEvent && (
              <p className="text-sm text-gray-500">Select an event to inspect it in detail.</p>
            )}
            {selectedEvent && (
              <>
                <EventReadableDetail event={selectedEvent} />
                <div>
                  <p className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Raw data
                  </p>
                  <JsonViewer data={selectedEvent} />
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function EventReadableDetail({ event }: { event: TraceEvent }) {
  const narrative = describeEvent(event);
  return (
    <div>
      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{narrative.headline}</p>
      {narrative.detail && (
        <p className="mt-1 whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-300">
          {narrative.detail}
        </p>
      )}
    </div>
  );
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}
