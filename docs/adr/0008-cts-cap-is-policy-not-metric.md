# ADR-008: The critical-failure cap is a deployment policy, not part of the CTS metric

## Status
Accepted

## Context
PROJECT_SPEC_3 §85-86 says that when Security, Tool Faithfulness, or Execution Integrity scores at
or below 29.9, the Composite Trust Score is clamped to a maximum of 30 ("critical failure cap").
Before this ADR, `CTSCalculator.compute()` (`backend/app/evaluation/scoring/cts.py`) applied that
clamp once, to the aggregated score, and returned only the clamped number as `cts` -- the uncapped
weighted sum existed only as `metadata["raw_cts"]`, an internal debugging value nothing downstream
read.

That single clamped number was then the only thing persisted (`evaluation_reports.cts`) and the
only thing every aggregation read: `EvaluationReportRepository.average_cts()` averaged it directly,
and the API/frontend only ever displayed it. Two runs with a security score of 29 and a security
score of 2 both reported CTS 30 -- ordering between them was destroyed, and any mean taken over a
set of such runs was a mean over clamped numbers, which is not a meaningful statistic: clamping is
a nonlinear, order-losing transform, so it does not commute with averaging or comparison.

## Decision
The critical-failure cap is a *deployment policy* layered on top of the CTS metric, not part of
the metric itself. The metric is `cts_raw`: the uncapped weighted sum of evaluator scores,
monotonic in every input, safe to average/compare/correlate across runs. The cap produces a
*second*, derived number, `cts_reported`, computed as `min(cts_raw, 30)` only when one of the
hard-cap evaluators (`security`, `tool_faithfulness`, `integrity` i.e. Execution Integrity) is at
or below the 29.9 critical-failure threshold. `cts_reported` exists to answer one question --
"is this run safe to treat as trustworthy for a deploy/no-deploy call?" -- and is never fed back
into arithmetic.

Concretely:
- `CTSResult` and `EvaluationReportModel` carry `cts_raw`, `cts_reported`, `critical_failure`
  (bool), and `critical_failure_modules` (the hard-cap evaluator names that triggered the cap),
  instead of a single `cts` field.
- The cap can only lower `cts_raw` via `min()`; the clamped value is never substituted back into
  the weighted sum, and individual evaluator contributions (`evaluator_contributions`) are never
  clamped -- they always report each module's true score.
- Every cross-run read -- `EvaluationReportRepository.average_cts_raw()`, the dashboard's
  `average_cts_raw` summary stat, `ComparePage`'s two-run comparison -- uses `cts_raw`.
- Every single-run decision surface -- the Run Details / Evaluation Report pages, the
  Markdown export -- shows `cts_reported` prominently (with a critical-failure badge naming the
  triggering modules), and shows `cts_raw` alongside it, explicitly labelled as the uncapped
  score, so a reviewer can still see how close to the cap a critically-failed run actually was.

## Consequences
- Analysis code (means, correlations, trend charts, model/task comparisons) must always read
  `cts_raw`; reading `cts_reported` for anything but a single run's headline number is a bug.
- The 0005 migration cannot recover `cts_raw` for rows persisted before this change, since only
  the clamped value was ever stored -- those rows backfill `cts_raw` to the old `cts` value and
  `critical_failure`/`critical_failure_modules` to `False`/`[]`. This is consistent (it does not
  invent capping that wasn't recorded) but slightly overstates that no historical run had a
  critical failure; re-evaluating historical runs (`POST /runs/{id}/evaluate` is idempotent and
  re-runnable) regenerates accurate values.
- If the cap's threshold or the hard-cap evaluator set ever changes, only `cts_reported`
  derivation changes -- `cts_raw` and its aggregations are unaffected, since they never depended
  on the cap in the first place.
