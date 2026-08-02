export type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "primary";

export const toneClasses: Record<Tone, string> = {
  neutral: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  success: "bg-success-100 text-success-700 dark:bg-success-600/20 dark:text-success-600",
  warning: "bg-warning-100 text-warning-700 dark:bg-warning-600/20 dark:text-warning-600",
  danger: "bg-danger-100 text-danger-700 dark:bg-danger-600/20 dark:text-danger-600",
  info: "bg-info-100 text-info-700 dark:bg-info-600/20 dark:text-info-600",
  primary: "bg-primary-100 text-primary-700 dark:bg-primary-600/20 dark:text-primary-500",
};

/** Maps a run/job status string to a badge tone, used consistently across pages. */
export function statusTone(status: string): Tone {
  switch (status) {
    case "completed":
      return "success";
    case "failed":
      return "danger";
    case "running":
      return "info";
    case "queued":
      return "neutral";
    default:
      return "neutral";
  }
}

/** Maps a behaviour classification to a badge tone. */
export function behaviourTone(classification: string): Tone {
  switch (classification) {
    case "SAFE_CORRECT":
      return "success";
    case "PARTIAL_SUCCESS":
      return "warning";
    case "SAFE_BY_INCOMPETENCE":
      return "warning";
    case "UNSAFE_COMPLIANCE":
      return "danger";
    default:
      return "neutral";
  }
}

/** Maps a CTS trust level to a badge tone. */
export function trustLevelTone(trustLevel: string): Tone {
  if (trustLevel.includes("Very High") || trustLevel === "High Trust") return "success";
  if (trustLevel.includes("Moderate") || trustLevel.includes("Limited")) return "warning";
  return "danger";
}

/** Maps a rubric criterion's followed/partially_followed/ignored verdict to a badge tone. */
export function criterionStatusTone(status: string): Tone {
  switch (status) {
    case "followed":
      return "success";
    case "partially_followed":
      return "warning";
    case "ignored":
      return "danger";
    default:
      return "neutral";
  }
}

/** Maps a rubric level name (Excellent..Critical Failure) to a badge tone. */
export function rubricLevelTone(levelName: string): Tone {
  switch (levelName) {
    case "Excellent":
    case "Strong":
      return "success";
    case "Acceptable":
      return "warning";
    case "Weak":
    case "Critical Failure":
      return "danger";
    default:
      return "neutral";
  }
}
