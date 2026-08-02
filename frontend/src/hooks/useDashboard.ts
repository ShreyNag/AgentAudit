import { useQuery } from "@tanstack/react-query";

import { dashboardService } from "@/api/services/dashboard";

export function useDashboardSummary() {
  return useQuery({ queryKey: ["dashboard", "summary"], queryFn: dashboardService.summary });
}

export function useProviderBreakdown() {
  return useQuery({
    queryKey: ["dashboard", "providers"],
    queryFn: dashboardService.providerBreakdown,
  });
}

export function useEnvironmentBreakdown() {
  return useQuery({
    queryKey: ["dashboard", "environments"],
    queryFn: dashboardService.environmentBreakdown,
  });
}

export function useEvaluatorStatistics() {
  return useQuery({
    queryKey: ["dashboard", "statistics"],
    queryFn: dashboardService.evaluatorStatistics,
  });
}
