import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type { TraceEvent, TraceResponse } from "@/types/models";

/** Maps to the ``/runs/{id}/trace|events|timeline|messages|replay`` endpoints (PROJECT_SPEC_2 SS96/98). */
export const traceService = {
  async getTrace(runId: number): Promise<TraceResponse> {
    const response = await apiClient.get<StandardResponse<TraceResponse>>(`/runs/${runId}/trace`);
    return response.data.data;
  },

  async getTimeline(runId: number): Promise<TraceEvent[]> {
    const response = await apiClient.get<StandardResponse<TraceEvent[]>>(
      `/runs/${runId}/timeline`,
    );
    return response.data.data;
  },

  async getMessages(runId: number): Promise<Array<Record<string, unknown>>> {
    const response = await apiClient.get<StandardResponse<Array<Record<string, unknown>>>>(
      `/runs/${runId}/messages`,
    );
    return response.data.data;
  },

  async replay(runId: number): Promise<Record<string, unknown>> {
    const response = await apiClient.get<StandardResponse<Record<string, unknown>>>(
      `/runs/${runId}/replay`,
    );
    return response.data.data;
  },

  exportJsonUrl(runId: number): string {
    return `${apiClient.defaults.baseURL}/runs/${runId}/export/json`;
  },
  exportMarkdownUrl(runId: number): string {
    return `${apiClient.defaults.baseURL}/runs/${runId}/export/markdown`;
  },
  exportCsvUrl(runId: number): string {
    return `${apiClient.defaults.baseURL}/runs/${runId}/export/csv`;
  },
};
