import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useLaunchRun } from "@/hooks/useRuns";
import type { BenchmarkTask } from "@/types/models";

interface LaunchBenchmarkDialogProps {
  task: BenchmarkTask | null;
  onClose: () => void;
}

/**
 * The Benchmark Launcher (PROJECT_SPEC_4 SS44-46). Always runs against the AUT/Judge
 * configured in .env -- provider/model are not user-selectable here (PROJECT_SPEC_1 SS15:
 * switching providers is a config change, not a per-run choice).
 */
export function LaunchBenchmarkDialog({ task, onClose }: LaunchBenchmarkDialogProps) {
  const navigate = useNavigate();
  const launchRun = useLaunchRun();
  const [error, setError] = useState<string | null>(null);

  if (!task) return null;

  const handleLaunch = async () => {
    setError(null);
    try {
      const run = await launchRun.mutateAsync({ task_id: task.task_id });
      onClose();
      navigate(`/runs/${run.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Dialog open={Boolean(task)} onClose={onClose} title={`Launch: ${task.title}`}>
      <div className="space-y-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{task.instruction}</p>

        {error && <p className="text-sm text-danger-600">Failed to launch: {error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="button" loading={launchRun.isPending} onClick={handleLaunch}>
            Launch
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
