import { Badge } from "@/components/ui/Badge";
import { describeEvent } from "@/features/trace/eventNarrative";
import { eventIconFor, eventTone } from "@/features/trace/eventIcons";
import { formatDateTime } from "@/lib/format";
import type { TraceEvent } from "@/types/models";

interface TimelineEventCardProps {
  event: TraceEvent;
  selected: boolean;
  onSelect: () => void;
}

/** One expandable card on the execution timeline (PROJECT_SPEC_4 SS70/SS72). */
export function TimelineEventCard({ event, selected, onSelect }: TimelineEventCardProps) {
  const Icon = eventIconFor(event.event_type);
  const narrative = describeEvent(event);

  return (
    <button
      onClick={onSelect}
      className={`flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
        selected
          ? "border-primary-500 bg-primary-50 dark:bg-primary-600/10"
          : "border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/60"
      }`}
    >
      <div className="mt-0.5 rounded-full bg-gray-100 p-1.5 dark:bg-gray-800">
        <Icon className="h-3.5 w-3.5 text-gray-600 dark:text-gray-300" aria-hidden="true" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {event.event_type}
          </span>
          <Badge tone={eventTone(event.status)}>{event.status}</Badge>
          {event.latency !== null && (
            <span className="text-xs text-gray-400">{Math.round(event.latency * 1000)}ms</span>
          )}
        </div>
        <p className="mt-0.5 text-xs text-gray-500">
          #{event.event_number} · {event.component} · {formatDateTime(event.timestamp)}
        </p>
        <p className="mt-1 line-clamp-2 text-xs text-gray-600 dark:text-gray-300">
          {narrative.headline}
          {narrative.detail && <span className="text-gray-400"> {narrative.detail}</span>}
        </p>
      </div>
    </button>
  );
}
