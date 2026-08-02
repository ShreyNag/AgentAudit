import { Beaker } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { LaunchBenchmarkDialog } from "@/features/benchmark/LaunchBenchmarkDialog";
import { useBenchmarks, useEnvironments } from "@/hooks/useBenchmarks";
import type { BenchmarkTask } from "@/types/models";

/** Browse and launch benchmark tasks (PROJECT_SPEC_4 SS41-46). */
export default function BenchmarksPage() {
  const [environment, setEnvironment] = useState<string | undefined>(undefined);
  const [selectedTask, setSelectedTask] = useState<BenchmarkTask | null>(null);
  const environments = useEnvironments();
  const tasks = useBenchmarks(environment);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant={environment === undefined ? "primary" : "secondary"}
          size="sm"
          onClick={() => setEnvironment(undefined)}
        >
          All
        </Button>
        {environments.data?.map((env) => (
          <Button
            key={env.name}
            variant={environment === env.name ? "primary" : "secondary"}
            size="sm"
            onClick={() => setEnvironment(env.name)}
          >
            {env.name}
          </Button>
        ))}
      </div>

      {tasks.isLoading && <SkeletonTable rows={4} />}
      {tasks.isError && <ErrorState error={tasks.error} onRetry={() => tasks.refetch()} />}
      {tasks.data && tasks.data.length === 0 && (
        <EmptyState
          icon={Beaker}
          title="No benchmarks available"
          description="Benchmark tasks are seeded automatically the first time they're requested."
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tasks.data?.map((task) => (
          <Card key={task.task_id}>
            <CardContent className="space-y-3 pt-5">
              <div className="flex items-center justify-between">
                <Badge tone="primary">{task.environment}</Badge>
                <Badge tone="neutral">{task.difficulty}</Badge>
              </div>
              <div>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{task.title}</p>
                <p className="mt-1 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">
                  {task.description}
                </p>
              </div>
              <Button size="sm" className="w-full" onClick={() => setSelectedTask(task)}>
                Launch
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <LaunchBenchmarkDialog task={selectedTask} onClose={() => setSelectedTask(null)} />
    </div>
  );
}
