import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type { Run } from "@/types/models";

export interface ListRunsParams {
  page?: number;
  page_size?: number;
  status?: string;
  provider?: string;
  environment?: string;
}

export interface ListRunsResult {
  runs: Run[];
  totalItems: number;
  totalPages: number;
}

/** Maps directly to the ``/runs`` backend endpoints (PROJECT_SPEC_2 SS94-95). */
export const runsService = {
  async list(params: ListRunsParams = {}): Promise<ListRunsResult> {
    const response = await apiClient.get<StandardResponse<Run[]>>("/runs", { params });
    const metadata = response.data.metadata as { total_items?: number; total_pages?: number };
    return {
      runs: response.data.data,
      totalItems: metadata.total_items ?? response.data.data.length,
      totalPages: metadata.total_pages ?? 1,
    };
  },

  async get(runId: number): Promise<Run> {
    const response = await apiClient.get<StandardResponse<Run>>(`/runs/${runId}`);
    return response.data.data;
  },

  async getStatus(runId: number): Promise<string> {
    const response = await apiClient.get<StandardResponse<{ status: string }>>(
      `/runs/${runId}/status`,
    );
    return response.data.data.status;
  },

  async remove(runId: number): Promise<void> {
    await apiClient.delete(`/runs/${runId}`);
  },

  async launch(params: { task_id: string }): Promise<Run> {
    // /benchmarks/run blocks until the entire multi-turn execution finishes (no background-job
    // model yet), which can take minutes against a slow/local model -- the shared client's 30s
    // default is tuned for normal fast endpoints and is too short for this one specifically.
    const response = await apiClient.post<StandardResponse<Run>>("/benchmarks/run", params, {
      timeout: 600_000,
    });
    return response.data.data;
  },
};
