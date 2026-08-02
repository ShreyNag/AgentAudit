import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

import { titleCase } from "@/lib/format";
import type { EvaluationScore } from "@/types/models";

/** Radar visualization of all ten evaluator scores (PROJECT_SPEC_4 SS102). */
export function ScoreRadarChart({ scores }: { scores: EvaluationScore[] }) {
  const data = scores.map((score) => ({
    evaluator: titleCase(score.evaluator_name),
    score: score.score,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid />
        <PolarAngleAxis dataKey="evaluator" tick={{ fontSize: 11 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
        <Radar name="Score" dataKey="score" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.35} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
