import { ServerCrash } from "lucide-react";

import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/Button";

/** Standardized error view (PROJECT_SPEC_4 SS62/SS142). Never exposes stack traces. */
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof ApiError ? error.message : "Something went wrong.";
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-danger-100 bg-danger-100/40 px-6 py-12 text-center dark:border-danger-600/30 dark:bg-danger-600/10">
      <ServerCrash className="mb-3 h-8 w-8 text-danger-600" aria-hidden="true" />
      <p className="font-medium text-danger-700 dark:text-danger-600">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}
