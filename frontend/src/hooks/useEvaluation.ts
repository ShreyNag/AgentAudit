import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { evaluationService } from "@/api/services/evaluation";

export function useEvaluationScores(runId: number | undefined) {
  return useQuery({
    queryKey: ["evaluation-scores", runId],
    queryFn: () => evaluationService.getScores(runId!),
    enabled: runId !== undefined,
  });
}

export function useCts(runId: number | undefined) {
  return useQuery({
    queryKey: ["cts", runId],
    queryFn: () => evaluationService.getCts(runId!),
    enabled: runId !== undefined,
    retry: false,
  });
}

export function useBehaviour(runId: number | undefined) {
  return useQuery({
    queryKey: ["behaviour", runId],
    queryFn: () => evaluationService.getBehaviour(runId!),
    enabled: runId !== undefined,
    retry: false,
  });
}

export function useFailure(runId: number | undefined) {
  return useQuery({
    queryKey: ["failure", runId],
    queryFn: () => evaluationService.getFailure(runId!),
    enabled: runId !== undefined,
    retry: false,
  });
}

export function useRubrics() {
  return useQuery({
    queryKey: ["rubrics"],
    queryFn: () => evaluationService.getRubrics(),
    staleTime: Infinity, // static reference data, identical for every run
  });
}

export function useEvaluateRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: evaluationService.evaluate,
    onSuccess: (_data, runId) => {
      void queryClient.invalidateQueries({ queryKey: ["evaluation-scores", runId] });
      void queryClient.invalidateQueries({ queryKey: ["cts", runId] });
      void queryClient.invalidateQueries({ queryKey: ["behaviour", runId] });
      void queryClient.invalidateQueries({ queryKey: ["failure", runId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
