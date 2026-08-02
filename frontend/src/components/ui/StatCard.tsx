import type { LucideIcon } from "lucide-react";
import React from "react";

import { Card, CardContent } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  icon?: LucideIcon;
  tone?: "neutral" | "success" | "danger" | "warning";
}

const toneClasses = {
  neutral: "text-gray-900 dark:text-gray-100",
  success: "text-success-600",
  danger: "text-danger-600",
  warning: "text-warning-600",
};

/** A single dashboard summary metric (PROJECT_SPEC_4 SS35). */
export function StatCard({ label, value, icon: Icon, tone = "neutral" }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between pt-5">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
            {label}
          </p>
          <p className={cn("mt-1 text-2xl font-semibold", toneClasses[tone])}>{value}</p>
        </div>
        {Icon && (
          <div className="rounded-full bg-gray-100 p-2.5 dark:bg-gray-800">
            <Icon className="h-5 w-5 text-gray-500 dark:text-gray-400" aria-hidden="true" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
