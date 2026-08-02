import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { evaluationService } from "@/api/services/evaluation";
import { runsService } from "@/api/services/runs";
import { Badge } from "@/components/ui/Badge";
import { trustLevelTone } from "@/components/ui/badgeTones";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/Table";
import { formatScore, titleCase } from "@/lib/format";

/** Comparative View (PROJECT_SPEC_4 SS119-121): compare two runs side-by-side, read-only. */
export default function ComparePage() {
  const [runAId, setRunAId] = useState("");
  const [runBId, setRunBId] = useState("");
  const [activeIds, setActiveIds] = useState<{ a: number; b: number } | null>(null);

  const runA = useComparisonData(activeIds?.a);
  const runB = useComparisonData(activeIds?.b);

  const compare = () => {
    const a = Number(runAId);
    const b = Number(runBId);
    if (Number.isFinite(a) && Number.isFinite(b)) setActiveIds({ a, b });
  };

  const evaluatorNames = Array.from(
    new Set([
      ...(runA.data?.scores.map((s) => s.evaluator_name) ?? []),
      ...(runB.data?.scores.map((s) => s.evaluator_name) ?? []),
    ]),
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Select Runs to Compare</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Run A ID</label>
            <input
              value={runAId}
              onChange={(event) => setRunAId(event.target.value)}
              className="w-32 rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Run B ID</label>
            <input
              value={runBId}
              onChange={(event) => setRunBId(event.target.value)}
              className="w-32 rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
          </div>
          <button
            onClick={compare}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            Compare
          </button>
        </CardContent>
      </Card>

      {!activeIds && (
        <EmptyState title="No comparison selected" description="Enter two run IDs above to compare them." />
      )}

      {activeIds && runA.data && runB.data && (
        <Card>
          <CardHeader>
            <CardTitle>Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHead>
                <tr>
                  <TableHeaderCell>Metric</TableHeaderCell>
                  <TableHeaderCell>Run A ({activeIds.a})</TableHeaderCell>
                  <TableHeaderCell>Run B ({activeIds.b})</TableHeaderCell>
                </tr>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">CTS</TableCell>
                  <TableCell>{formatScore(runA.data.cts?.cts)}</TableCell>
                  <TableCell>{formatScore(runB.data.cts?.cts)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Trust Level</TableCell>
                  <TableCell>
                    {runA.data.cts && (
                      <Badge tone={trustLevelTone(runA.data.cts.trust_level)}>
                        {runA.data.cts.trust_level}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {runB.data.cts && (
                      <Badge tone={trustLevelTone(runB.data.cts.trust_level)}>
                        {runB.data.cts.trust_level}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Status</TableCell>
                  <TableCell>{runA.data.run.status}</TableCell>
                  <TableCell>{runB.data.run.status}</TableCell>
                </TableRow>
                {evaluatorNames.map((name) => (
                  <TableRow key={name}>
                    <TableCell className="font-medium">{titleCase(name)}</TableCell>
                    <TableCell>
                      {formatScore(runA.data.scores.find((s) => s.evaluator_name === name)?.score)}
                    </TableCell>
                    <TableCell>
                      {formatScore(runB.data.scores.find((s) => s.evaluator_name === name)?.score)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function useComparisonData(runId: number | undefined) {
  return useQuery({
    queryKey: ["compare", runId],
    queryFn: async () => {
      const run = await runsService.get(runId!);
      const scores = await evaluationService.getScores(runId!).catch(() => []);
      const cts = await evaluationService.getCts(runId!).catch(() => null);
      return { run, scores, cts };
    },
    enabled: runId !== undefined && Number.isFinite(runId),
  });
}
