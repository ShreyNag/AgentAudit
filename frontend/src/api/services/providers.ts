import { apiClient } from "@/api/client";
import type { StandardResponse } from "@/types/api";
import type { ProviderHealth } from "@/types/models";

/** Maps to the ``/providers`` endpoints (PROJECT_SPEC_2 SS101). */
export const providersService = {
  async list(): Promise<string[]> {
    const response = await apiClient.get<StandardResponse<string[]>>("/providers");
    return response.data.data;
  },

  async health(): Promise<{ aut: ProviderHealth; judge: ProviderHealth }> {
    const response =
      await apiClient.get<StandardResponse<{ aut: ProviderHealth; judge: ProviderHealth }>>(
        "/providers/health",
      );
    return response.data.data;
  },
};
