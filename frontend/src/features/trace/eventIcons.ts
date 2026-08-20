import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  Layers,
  MessageSquare,
  Play,
  Wrench,
  XCircle,
  type LucideIcon,
} from "lucide-react";

/** Maps a trace event type (PROJECT_SPEC_6 SS52) to an icon and semantic tone. */
export function eventIconFor(eventType: string): LucideIcon {
  if (eventType.startsWith("Run")) {
    if (eventType === "RunFailed") return XCircle;
    if (eventType === "RunCompleted") return CheckCircle2;
    return Play;
  }
  if (eventType.startsWith("Tool")) return Wrench;
  if (eventType.startsWith("Provider")) return MessageSquare;
  if (eventType === "ReasoningGenerated" || eventType === "PlannerStep") return Brain;
  if (eventType === "AgentStep") return Layers;
  if (eventType === "Warning") return AlertTriangle;
  if (eventType === "Error") return XCircle;
  return Bot;
}

export function eventTone(status: string): "success" | "danger" | "warning" | "neutral" {
  if (status === "failed" || status === "error") return "danger";
  if (status === "warning") return "warning";
  if (status === "ok" || status === "completed") return "success";
  return "neutral";
}
