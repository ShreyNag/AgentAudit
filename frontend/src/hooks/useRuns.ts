import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { runsService, type ListRunsParams } from "@/api/services/runs";

export function useRuns(params: ListRunsParams = {}) {
  return useQuery({
    queryKey: ["runs", params],
    queryFn: () => runsService.list(params),
  });
}

export function useRun(runId: number | undefined) {
  return useQuery({
    queryKey: ["run", runId],
    queryFn: () => runsService.get(runId!),
    enabled: runId !== undefined,
  });
}

/**
 * Polls for a run by ``run_uuid`` until AgentAudit observes it -- powers the "Waiting for
 * agent" state on the Independent Agents page, for a run_id generated client-side before any
 * trace exists. Stops polling as soon as the run is found (or ``enabled`` is false).
 */
export function useRunByUuid(runUuid: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["run-by-uuid", runUuid],
    queryFn: () => runsService.getByUuid(runUuid!),
    enabled: enabled && runUuid !== undefined,
    refetchInterval: (query) => (query.state.data ? false : 3_000),
  });
}

export function useLaunchRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runsService.launch,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runsService.remove,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
  });
}
