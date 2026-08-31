/** Frontend TypeScript models, mirroring backend response schemas (PROJECT_SPEC_4 SS18). */

/** "benchmark": AgentAudit drove the execution. "external": an independently running agent was
 * only observed (app.trace.tracer.AgentAuditTracer) -- see docs/external-agent-tracing-guide.md. */
export type ExecutionMode = "benchmark" | "external";

export interface Run {
  id: number;
  run_uuid: string;
  benchmark_task_id: number;
  provider: string;
  model: string;
  judge_provider: string | null;
  judge_model: string | null;
  environment: string;
  status: string;
  execution_mode: ExecutionMode;
  execution_time: number | null;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
}

export interface BenchmarkTask {
  task_id: string;
  title: string;
  description: string;
  environment: string;
  difficulty: string;
  attack_type: string | null;
  instruction: string;
  expected_tool_sequence: string[];
  created_at: string;
}

export interface BenchmarkEnvironment {
  name: string;
  description: string;
  version: string;
  toolset: string[];
  difficulty_levels: string[];
}

export interface TraceResponse {
  run_id: number;
  planner: Record<string, unknown>;
  reasoning: Record<string, unknown>;
  messages: Array<Record<string, unknown>>;
  /** For an externally observed run: may carry agent_name, agent_id, task_id, parent_run_id,
   * source ("external_agent"). Empty for an AgentAudit-driven benchmark run. */
  metadata: Record<string, unknown>;
  statistics: Record<string, unknown>;
  version: string;
  created_at: string;
}

export interface TraceEvent {
  event_number: number;
  timestamp: string;
  event_type: string;
  component: string;
  payload: Record<string, unknown>;
  latency: number | null;
  status: string;
}

export type CriterionStatus = "followed" | "partially_followed" | "ignored";

export interface CriterionAssessment {
  criterion: string;
  status: CriterionStatus;
  justification: string;
}

export interface EvaluationScore {
  evaluator_name: string;
  score: number;
  confidence: number;
  reasoning: string;
  expected_outcome: string;
  actual_outcome: string;
  evidence: Array<Record<string, unknown>>;
  rubric_level: string;
  matched_criteria: string[];
  criteria_assessment: CriterionAssessment[];
  created_at: string;
}

export interface RubricLevel {
  level: number;
  name: string;
  min_score: number;
  max_score: number;
  description: string;
}

export interface Rubric {
  identifier: string;
  description: string;
  criteria: string[];
  levels: RubricLevel[];
  failure_conditions: string[];
}

export interface EvaluationReport {
  run_id: number;
  overall_reasoning: string;
  overall_summary: string;
  cts: number;
  planner_summary: string | null;
  security_summary: string | null;
  integrity_summary: string | null;
  created_at: string;
}

export interface BehaviourReport {
  classification: "SAFE_CORRECT" | "SAFE_BY_INCOMPETENCE" | "UNSAFE_COMPLIANCE" | "PARTIAL_SUCCESS";
  confidence: number;
  reasoning: string;
  evidence: string[];
  created_at: string;
}

export interface FailureReport {
  primary_failure: string;
  secondary_failures: string[];
  affected_components: string[];
  diagnostic_reasoning: string;
  confidence: number;
  created_at: string;
}

export interface CTSSummary {
  run_id: number;
  cts: number;
  trust_level: string;
}

export interface DashboardSummary {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  running_runs: number;
  average_cts: number | null;
}

export interface GroupedCount {
  label: string;
  count: number;
}

export interface EvaluatorStatistic {
  evaluator_name: string;
  average_score: number;
  average_confidence: number;
  count: number;
}

export interface ProviderHealth {
  provider: string;
  healthy: boolean;
  message: string | null;
  latency: number | null;
}

