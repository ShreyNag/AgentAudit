import { useQuery } from "@tanstack/react-query";

import { traceService } from "@/api/services/trace";

export function useTrace(runId: number | undefined) {
  return useQuery({
    queryKey: ["trace", runId],
    queryFn: () => traceService.getTrace(runId!),
    enabled: runId !== undefined,
  });
}

export function useTimeline(runId: number | undefined) {
  return useQuery({
    queryKey: ["timeline", runId],
    queryFn: () => traceService.getTimeline(runId!),
    enabled: runId !== undefined,
  });
}

export function useReplay(runId: number | undefined) {
  return useQuery({
    queryKey: ["replay", runId],
    queryFn: () => traceService.replay(runId!),
    enabled: false, // fetched on demand when the user opens Replay mode
  });
}
