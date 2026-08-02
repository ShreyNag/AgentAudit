import { CheckCircle2, ChevronDown, ChevronUp, CircleDashed, XCircle } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { criterionStatusTone, rubricLevelTone } from "@/components/ui/badgeTones";
import { formatPercent, formatScore, titleCase } from "@/lib/format";
import type { CriterionStatus, EvaluationScore, Rubric } from "@/types/models";

function scoreTone(score: number): "success" | "warning" | "danger" {
  if (score >= 70) return "success";
  if (score >= 50) return "warning";
  return "danger";
}

const STATUS_LABEL: Record<CriterionStatus, string> = {
  followed: "Followed",
  partially_followed: "Partially Followed",
  ignored: "Ignored",
};

function StatusIcon({ status }: { status: CriterionStatus }) {
  if (status === "followed") return <CheckCircle2 className="h-4 w-4 text-success-600" aria-hidden="true" />;
  if (status === "ignored") return <XCircle className="h-4 w-4 text-danger-600" aria-hidden="true" />;
  return <CircleDashed className="h-4 w-4 text-warning-600" aria-hidden="true" />;
}

/** One evaluator's expandable detail section (PROJECT_SPEC_4 SS105-106). */
export function EvaluatorCard({ score, rubric }: { score: EvaluationScore; rubric?: Rubric }) {
  const [expanded, setExpanded] = useState(true);

  // Every rubric criterion, paired with its followed/partially_followed/ignored verdict when the
  // Judge produced one (older, already-persisted runs may predate this field).
  const criteriaRows = (rubric?.criteria ?? []).map((criterion) => ({
    criterion,
    assessment: score.criteria_assessment.find((item) => item.criterion === criterion),
  }));

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800">
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        aria-expanded={expanded}
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {titleCase(score.evaluator_name)}
            </span>
            <Badge tone={scoreTone(score.score)}>{formatScore(score.score)}/100</Badge>
            <Badge tone={rubricLevelTone(score.rubric_level)}>{score.rubric_level}</Badge>
            <span className="text-xs text-gray-400">
              Confidence {formatPercent(score.confidence)}
            </span>
          </div>
          {!expanded && score.reasoning && (
            <p className="mt-1 line-clamp-1 text-xs text-gray-500 dark:text-gray-400">
              Reason: {score.reasoning}
            </p>
          )}
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 shrink-0" /> : <ChevronDown className="h-4 w-4 shrink-0" />}
      </button>
      {expanded && (
        <div className="space-y-4 border-t border-gray-100 px-4 py-3 text-sm dark:border-gray-800">
          {rubric?.description && (
            <p className="text-xs italic text-gray-500 dark:text-gray-400">{rubric.description}</p>
          )}

          {(score.expected_outcome || score.actual_outcome) && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {score.expected_outcome && (
                <div>
                  <p className="font-medium">Expected</p>
                  <p className="text-gray-600 dark:text-gray-300">{score.expected_outcome}</p>
                </div>
              )}
              {score.actual_outcome && (
                <div>
                  <p className="font-medium">Actual</p>
                  <p className="text-gray-600 dark:text-gray-300">{score.actual_outcome}</p>
                </div>
              )}
            </div>
          )}

          <div>
            <p className="font-medium">Why this score</p>
            <p className="text-gray-600 dark:text-gray-300">{score.reasoning}</p>
          </div>

          {criteriaRows.length > 0 ? (
            <div>
              <p className="font-medium">Rubric Criteria</p>
              <ul className="mt-1 space-y-2">
                {criteriaRows.map(({ criterion, assessment }) => (
                  <li key={criterion} className="flex items-start gap-2">
                    {assessment ? (
                      <StatusIcon status={assessment.status} />
                    ) : (
                      <CircleDashed className="h-4 w-4 text-gray-300 dark:text-gray-600" aria-hidden="true" />
                    )}
                    <div className="min-w-0">
                      <span className="text-gray-800 dark:text-gray-200">{criterion}</span>
                      {assessment && (
                        <>
                          {" "}
                          <Badge tone={criterionStatusTone(assessment.status)} className="align-middle text-[10px]">
                            {STATUS_LABEL[assessment.status]}
                          </Badge>
                        </>
                      )}
                      {assessment?.justification && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {assessment.justification}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            score.matched_criteria.length > 0 && (
              <div>
                <p className="font-medium">Matched Criteria</p>
                <ul className="ml-4 list-disc text-gray-600 dark:text-gray-300">
                  {score.matched_criteria.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )
          )}

          {rubric && rubric.levels.length > 0 && (
            <div>
              <p className="font-medium">Scoring Scale</p>
              <ul className="mt-1 space-y-1">
                {rubric.levels.map((level) => (
                  <li
                    key={level.name}
                    className={`flex items-center gap-2 rounded px-1.5 py-0.5 ${
                      level.name === score.rubric_level ? "bg-gray-100 dark:bg-gray-800" : ""
                    }`}
                  >
                    <Badge tone={rubricLevelTone(level.name)} className="w-28 shrink-0 justify-center">
                      {level.name}
                    </Badge>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {level.min_score}-{level.max_score}: {level.description}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {score.evidence.length > 0 && (
            <div>
              <p className="font-medium">Evidence</p>
              <ul className="ml-4 list-disc text-gray-600 dark:text-gray-300">
                {score.evidence.map((item, index) => (
                  <li key={index}>{String(item.description ?? JSON.stringify(item))}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
