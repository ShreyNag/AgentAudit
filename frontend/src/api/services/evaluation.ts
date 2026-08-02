import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type {
  BehaviourReport,
  CTSSummary,
  EvaluationReport,
  EvaluationScore,
  FailureReport,
  Rubric,
} from "@/types/models";

/** Maps to the ``/runs/{id}/evaluate|evaluation|cts|behaviour|failure`` endpoints (PROJECT_SPEC_2 SS97). */
export const evaluationService = {
  async evaluate(runId: number): Promise<EvaluationReport> {
    // /evaluate blocks until all ten evaluators' Judge calls finish -- against a local/slow
    // model (e.g. Ollama) that easily exceeds the shared client's 30s default, same reasoning
    // as runsService.launch().
    const response = await apiClient.post<StandardResponse<EvaluationReport>>(
      `/runs/${runId}/evaluate`,
      undefined,
      { timeout: 600_000 },
    );
    return response.data.data;
  },

  async getScores(runId: number): Promise<EvaluationScore[]> {
    const response = await apiClient.get<StandardResponse<EvaluationScore[]>>(
      `/runs/${runId}/evaluation`,
    );
    return response.data.data;
  },

  async getCts(runId: number): Promise<CTSSummary> {
    const response = await apiClient.get<StandardResponse<CTSSummary>>(`/runs/${runId}/cts`);
    return response.data.data;
  },

  async getBehaviour(runId: number): Promise<BehaviourReport> {
    const response = await apiClient.get<StandardResponse<BehaviourReport>>(
      `/runs/${runId}/behaviour`,
    );
    return response.data.data;
  },

  async getFailure(runId: number): Promise<FailureReport | null> {
    try {
      const response = await apiClient.get<StandardResponse<FailureReport>>(
        `/runs/${runId}/failure`,
      );
      return response.data.data;
    } catch {
      return null;
    }
  },

  async getRubrics(): Promise<Record<string, Rubric>> {
    const response = await apiClient.get<StandardResponse<Record<string, Rubric>>>(
      "/evaluators/rubrics",
    );
    return response.data.data;
  },
};
