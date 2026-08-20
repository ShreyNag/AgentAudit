import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type { DashboardSummary, EvaluatorStatistic, GroupedCount } from "@/types/models";

/** Maps to the ``/dashboard`` endpoints (PROJECT_SPEC_2 SS99). */
export const dashboardService = {
  async summary(): Promise<DashboardSummary> {
    const response = await apiClient.get<StandardResponse<DashboardSummary>>("/dashboard/summary");
    return response.data.data;
  },

  async providerBreakdown(): Promise<GroupedCount[]> {
    const response = await apiClient.get<StandardResponse<GroupedCount[]>>("/dashboard/providers");
    return response.data.data;
  },

  async environmentBreakdown(): Promise<GroupedCount[]> {
    const response = await apiClient.get<StandardResponse<GroupedCount[]>>(
      "/dashboard/environments",
    );
    return response.data.data;
  },

  async executionModeBreakdown(): Promise<GroupedCount[]> {
    const response = await apiClient.get<StandardResponse<GroupedCount[]>>(
      "/dashboard/execution-modes",
    );
    return response.data.data;
  },

  async evaluatorStatistics(): Promise<EvaluatorStatistic[]> {
    const response = await apiClient.get<StandardResponse<EvaluatorStatistic[]>>(
      "/dashboard/statistics",
    );
    return response.data.data;
  },
};
