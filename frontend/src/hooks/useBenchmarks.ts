import { useQuery } from "@tanstack/react-query";

import { benchmarksService } from "@/api/services/benchmarks";

export function useBenchmarks(environment?: string) {
  return useQuery({
    queryKey: ["benchmarks", environment],
    queryFn: () => benchmarksService.list(environment),
  });
}

export function useBenchmark(taskId: string | undefined) {
  return useQuery({
    queryKey: ["benchmark", taskId],
    queryFn: () => benchmarksService.get(taskId!),
    enabled: taskId !== undefined,
  });
}

export function useEnvironments() {
  return useQuery({
    queryKey: ["environments"],
    queryFn: () => benchmarksService.listEnvironments(),
  });
}
