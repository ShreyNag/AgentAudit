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
