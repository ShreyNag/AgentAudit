import axios, { AxiosError } from "axios";

import type { ApiErrorBody } from "@/types/api";

/**
 * The single shared Axios client (PROJECT_SPEC_4 SS15). Components never call Axios directly --
 * only api/services/*.ts modules import this client.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  config.headers["X-Request-ID"] = crypto.randomUUID();
  return config;
});

/** A normalized, typed application error surfaced from any failed API call. */
export class ApiError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly requestId: string | null;
  readonly status: number | null;

  constructor(body: ApiErrorBody, status: number | null) {
    super(body.message);
    this.name = "ApiError";
    this.code = body.code;
    this.details = body.details;
    this.requestId = body.request_id;
    this.status = status;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.data && typeof error.response.data === "object" && "code" in error.response.data) {
      return Promise.reject(new ApiError(error.response.data, error.response.status ?? null));
    }
    return Promise.reject(
      new ApiError(
        {
          status: "error",
          code: error.code ?? "NETWORK_ERROR",
          message: error.message || "A network error occurred.",
          details: {},
          request_id: null,
          timestamp: new Date().toISOString(),
        },
        error.response?.status ?? null,
      ),
    );
  },
);
