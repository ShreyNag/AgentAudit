import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import React from "react";

import { cn } from "@/lib/cn";

type Tone = "success" | "warning" | "danger" | "info";

const toneConfig: Record<Tone, { icon: React.ElementType; classes: string }> = {
  success: { icon: CheckCircle2, classes: "bg-success-100 text-success-700 dark:bg-success-600/10" },
  warning: { icon: AlertTriangle, classes: "bg-warning-100 text-warning-700 dark:bg-warning-600/10" },
  danger: { icon: XCircle, classes: "bg-danger-100 text-danger-700 dark:bg-danger-600/10" },
  info: { icon: Info, classes: "bg-info-100 text-info-700 dark:bg-info-600/10" },
};

interface AlertProps {
  tone: Tone;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

/** Distinguishes success/warning/error states visually (PROJECT_SPEC_4 SS22/SS139). */
export function Alert({ tone, title, description, action }: AlertProps) {
  const { icon: Icon, classes } = toneConfig[tone];
  return (
    <div className={cn("flex items-start gap-3 rounded-lg p-4", classes)} role="alert">
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="flex-1">
        <p className="font-medium">{title}</p>
        {description && <p className="mt-1 text-sm opacity-90">{description}</p>}
      </div>
      {action}
    </div>
  );
}
