import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";
import React from "react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

/** Explains why there's no content and suggests the next action (PROJECT_SPEC_4 SS61/SS141). */
export function EmptyState({ icon: Icon = Inbox, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 px-6 py-12 text-center dark:border-gray-700">
      <Icon className="mb-3 h-8 w-8 text-gray-400" aria-hidden="true" />
      <p className="font-medium text-gray-900 dark:text-gray-100">{title}</p>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-gray-500 dark:text-gray-400">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
