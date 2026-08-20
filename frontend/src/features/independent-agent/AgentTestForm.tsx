import { useState } from "react";

import { Button } from "@/components/ui/Button";
import type { AgentTestConfig } from "@/features/independent-agent/integrationSnippets";
import { useBenchmarks } from "@/hooks/useBenchmarks";
import { useProviderList } from "@/hooks/useProviders";
import { cn } from "@/lib/cn";

const INPUT_CLASS =
  "w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800";

export interface AgentTestFormValues {
  agentName: string;
  agentId: string;
  provider: string;
  model: string;
  traceSource: string;
  taskId: string;
  testInstructions: string;
  groundTruth: string;
  metadata: string;
}

const EMPTY_VALUES: AgentTestFormValues = {
  agentName: "",
  agentId: "",
  provider: "",
  model: "",
  traceSource: "",
  taskId: "",
  testInstructions: "",
  groundTruth: "",
  metadata: "",
};

interface AgentTestFormProps {
  onCreate: (config: AgentTestConfig, values: AgentTestFormValues) => void;
}

/**
 * Generates a run_id and integration instructions -- it does NOT launch, execute, or contact
 * the independent agent in any way (AgentAudit only observes). No run row exists in AgentAudit
 * until that agent itself submits a trace to POST /api/v1/runs/external.
 *
 * Fields are split into two groups matching the real API contract:
 *   - "Agent metadata" is never sent to the backend as-is; it only pre-fills the generated
 *     integration snippets below (agent_name/agent_id/environment ARE real AgentAuditTracer
 *     constructor params, but "Agent Endpoint / Trace Source" is a note for your own reference,
 *     not a field ExternalRunIngestRequest accepts).
 *   - "Task / evaluation context" maps directly to POST /api/v1/runs/external's real fields
 *     (task_id, task_instruction, ground_truth) once your agent actually submits its trace.
 */
export function AgentTestForm({ onCreate }: AgentTestFormProps) {
  const [values, setValues] = useState<AgentTestFormValues>(EMPTY_VALUES);
  const [error, setError] = useState<string | null>(null);
  const providers = useProviderList();
  const tasks = useBenchmarks();

  const set = <K extends keyof AgentTestFormValues>(key: K, value: AgentTestFormValues[K]) =>
    setValues((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!values.agentName.trim()) {
      setError("Agent Name is required.");
      return;
    }
    if (values.groundTruth.trim()) {
      try {
        JSON.parse(values.groundTruth);
      } catch {
        setError("Ground Truth must be valid JSON (or left blank).");
        return;
      }
    }
    if (values.metadata.trim()) {
      try {
        JSON.parse(values.metadata);
      } catch {
        setError("Metadata must be valid JSON (or left blank).");
        return;
      }
    }

    const config: AgentTestConfig = {
      runId: crypto.randomUUID(),
      agentName: values.agentName.trim(),
      agentId: values.agentId.trim(),
      provider: values.provider.trim(),
      model: values.model.trim(),
      taskId: values.taskId.trim(),
      traceSource: values.traceSource.trim(),
      environment: values.agentName.trim().toLowerCase().replace(/\s+/g, "_") || "independent_agent",
    };
    onCreate(config, values);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Agent metadata
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Field label="Agent Name" required>
            <input
              value={values.agentName}
              onChange={(event) => set("agentName", event.target.value)}
              placeholder="e.g. support-chatbot-v3"
              className={INPUT_CLASS}
            />
          </Field>
          <Field label="Agent ID (optional)">
            <input
              value={values.agentId}
              onChange={(event) => set("agentId", event.target.value)}
              placeholder="e.g. a deployment or version tag"
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Provider">
            <input
              list="independent-agent-providers"
              value={values.provider}
              onChange={(event) => set("provider", event.target.value)}
              placeholder="e.g. openai, anthropic, or your own"
              className={INPUT_CLASS}
            />
            <datalist id="independent-agent-providers">
              {providers.data?.map((name) => <option key={name} value={name} />)}
            </datalist>
            <p className="mt-1 text-xs text-gray-500">
              The LLM vendor your agent uses -- for labeling only. AgentAudit never calls it.
            </p>
          </Field>
          <Field label="Model">
            <input
              value={values.model}
              onChange={(event) => set("model", event.target.value)}
              placeholder="e.g. gpt-5, claude-sonnet-5"
              className={INPUT_CLASS}
            />
          </Field>

          <div className="md:col-span-2">
            <Field label="Agent Endpoint / Trace Source (optional)">
              <input
                value={values.traceSource}
                onChange={(event) => set("traceSource", event.target.value)}
                placeholder="e.g. runs on my laptop / a Lambda function / http://my-agent.internal"
                className={INPUT_CLASS}
              />
              <p className="mt-1 text-xs text-gray-500">
                For your own reference only -- included as a comment in the generated snippets
                below. AgentAudit's API has no such field: it never reaches out to your agent,
                your agent reaches out to it.
              </p>
            </Field>
          </div>
        </div>
      </div>

      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Task / evaluation context
        </p>
        <div className="space-y-4">
          <Field label="Task ID (optional)">
            <input
              list="independent-agent-tasks"
              value={values.taskId}
              onChange={(event) => set("taskId", event.target.value)}
              placeholder="e.g. trip_planner-001"
              className={INPUT_CLASS}
            />
            <datalist id="independent-agent-tasks">
              {tasks.data?.map((task) => <option key={task.task_id} value={task.task_id} />)}
            </datalist>
            <p className="mt-1 text-xs text-gray-500">
              {values.taskId && tasks.data?.some((t) => t.task_id === values.taskId)
                ? "Matches a registered benchmark task -- its real ground truth will be used."
                : "Leave blank, or use a custom id, for an arbitrary task with no fixed ground truth."}
            </p>
          </Field>

          <Field label="Test Instructions (optional)">
            <textarea
              value={values.testInstructions}
              onChange={(event) => set("testInstructions", event.target.value)}
              placeholder="What was the agent asked to do? Shown to the Judge when Task ID is blank or unregistered."
              rows={2}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Ground Truth / Expected Result (optional, JSON)">
            <textarea
              value={values.groundTruth}
              onChange={(event) => set("groundTruth", event.target.value)}
              placeholder='{"expected_outcome": "..."}'
              rows={2}
              className={cn(INPUT_CLASS, "font-mono text-xs")}
            />
            <p className="mt-1 text-xs text-gray-500">
              Only used when Task ID doesn't match a registered benchmark task. Never fabricated
              by AgentAudit -- if left blank, evaluation proceeds with no fixed ground truth.
            </p>
          </Field>

          <Field label="Metadata (optional, JSON)">
            <textarea
              value={values.metadata}
              onChange={(event) => set("metadata", event.target.value)}
              placeholder='{"framework": "langgraph"}'
              rows={2}
              className={cn(INPUT_CLASS, "font-mono text-xs")}
            />
          </Field>
        </div>
      </div>

      {error && <p className="text-sm text-danger-600">{error}</p>}

      <Button type="submit">Generate Run ID &amp; Instructions</Button>
    </form>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-gray-500">
        {label}
        {required && <span className="text-danger-600"> *</span>}
      </span>
      {children}
    </label>
  );
}
