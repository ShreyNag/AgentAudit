import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type { BenchmarkEnvironment, BenchmarkTask } from "@/types/models";

/** Maps to the ``/benchmarks`` and ``/environments`` endpoints (PROJECT_SPEC_2 SS94). */
export const benchmarksService = {
  async list(environment?: string): Promise<BenchmarkTask[]> {
    const response = await apiClient.get<StandardResponse<BenchmarkTask[]>>("/benchmarks", {
      params: environment ? { environment } : undefined,
    });
    return response.data.data;
  },

  async get(taskId: string): Promise<BenchmarkTask> {
    const response = await apiClient.get<StandardResponse<BenchmarkTask>>(`/benchmarks/${taskId}`);
    return response.data.data;
  },

  async listEnvironments(): Promise<BenchmarkEnvironment[]> {
    const response = await apiClient.get<StandardResponse<BenchmarkEnvironment[]>>("/environments");
    return response.data.data;
  },
};
