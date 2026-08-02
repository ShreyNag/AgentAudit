import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { describeEvent } from "@/features/trace/eventNarrative";
import { eventIconFor, eventTone } from "@/features/trace/eventIcons";
import { formatDateTime } from "@/lib/format";
import type { TraceEvent } from "@/types/models";

/**
 * The full execution trace, told as a plain-English story rather than raw event dumps -- "the
 * model decided to call this tool, here's what it called and with what, here's what came back" --
 * so a reviewer can read exactly how one execution cycle unfolded without touching raw JSON.
 */
export function TraceNarrativeList({ events }: { events: TraceEvent[] }) {
  if (events.length === 0) {
    return <EmptyState title="No events recorded" description="This run has no execution trace." />;
  }

  return (
    <ol className="relative space-y-0">
      {events.map((event, index) => {
        const Icon = eventIconFor(event.event_type);
        const narrative = describeEvent(event);
        const isLast = index === events.length - 1;
        return (
          <li key={event.event_number} className="relative flex gap-4 pb-6 last:pb-0">
            {!isLast && (
              <span
                aria-hidden="true"
                className="absolute left-[15px] top-8 h-[calc(100%-1.5rem)] w-px bg-gray-200 dark:bg-gray-800"
              />
            )}
            <div className="z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
              <Icon className="h-4 w-4 text-gray-600 dark:text-gray-300" aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                  Step {event.event_number}
                </span>
                <Badge tone={eventTone(event.status)} className="text-xs">
                  {event.status}
                </Badge>
                <span className="text-xs text-gray-400">{formatDateTime(event.timestamp)}</span>
                {event.latency !== null && (
                  <span className="text-xs text-gray-400">{Math.round(event.latency * 1000)}ms</span>
                )}
              </div>
              <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                {narrative.headline}
              </p>
              {narrative.detail && (
                <p className="mt-1 whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-300">
                  {narrative.detail}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
