import { ArrowDown, Bot, ChartBar, Radio, ScanEye, Trophy } from "lucide-react";

import { Card, CardContent } from "@/components/ui/Card";

const FLOW = [
  { label: "Your Independent Agent", icon: Bot },
  { label: "AgentAuditTracer", icon: Radio },
  { label: "External Trace API", icon: ScanEye },
  { label: "Evaluation Engine", icon: ChartBar },
  { label: "Trust Score", icon: Trophy },
];

/** Section 1 -- "How It Works". Purely explanatory, no data, no run: makes the architectural
 * separation (AgentAudit observes, it never drives) impossible to miss before anyone touches
 * the form below. */
export function HowItWorks() {
  return (
    <Card>
      <CardContent className="space-y-5 pt-5">
        <div>
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            How It Works
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Independent agents run outside AgentAudit's execution engine. The agent reports its
            execution trace to AgentAudit, which then evaluates the trace using the same
            evaluation engine used by benchmark runs.
          </p>
        </div>

        <div className="flex flex-col items-center gap-1">
          {FLOW.map((step, index) => (
            <div key={step.label} className="flex w-full max-w-xs flex-col items-center">
              <div className="flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5 dark:border-gray-800 dark:bg-gray-800/60">
                <step.icon className="h-4 w-4 shrink-0 text-primary-600" aria-hidden="true" />
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {step.label}
                </span>
              </div>
              {index < FLOW.length - 1 && (
                <ArrowDown className="my-1 h-4 w-4 text-gray-400" aria-hidden="true" />
              )}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
            <p className="mb-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
              AgentAudit-driven
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              The Benchmarks page. AgentAudit picks a task, calls the configured AUT provider,
              invokes the environment's tools, and records every step itself as it happens.
            </p>
          </div>
          <div className="rounded-lg border border-primary-200 bg-primary-50/40 p-4 dark:border-primary-600/30 dark:bg-primary-600/10">
            <p className="mb-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
              Independently-running agent
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              This page. Your agent runs entirely on its own -- its own LLM, tools, memory,
              execution loop, framework -- and reports what it did to AgentAudit's tracer.
              AgentAudit only observes and evaluates; it never launches or controls your agent.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
