/** Mirrors app.schemas.common.StandardResponse (PROJECT_SPEC_2 SS104). */
export interface StandardResponse<T> {
  status: "success" | "error";
  message: string;
  data: T;
  metadata: Record<string, unknown>;
  errors: string[] | null;
}

/** Mirrors app.schemas.common.PaginatedMetadata. */
export interface PaginatedMetadata {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

/** Mirrors the error envelope in app.middleware.exception_handlers. */
export interface ApiErrorBody {
  status: "error";
  code: string;
  message: string;
  details: Record<string, unknown>;
  request_id: string | null;
  timestamp: string;
}
