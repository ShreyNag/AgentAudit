# ADR-007: All 14 tables are created in the first migration

## Status
Accepted

## Context
PROJECT_SPEC_1 §76 lists 14 tables as "the initial implementation shall include," including four
evaluation-related tables (`evaluation_reports`, `evaluation_scores`, `behaviour_reports`,
`failure_reports`). PROJECT_SPEC_6 Part 5 Phase 3 ("Database Layer") also lists "Evaluations"
among the tables created in that phase, even though the Evaluation Engine itself isn't built
until Phase 9.

## Decision
Since the full system (including the Evaluation Engine) is in scope for this implementation,
there is no real conflict: the first Alembic migration creates all 14 tables up front, matching
both specs literally. `evaluation_reports`, `evaluation_scores`, `behaviour_reports`, and
`failure_reports` remain unwritten until Phase 9's `EvaluationService` exists, but the schema —
and therefore the "adding an evaluator requires inserting rows, not a migration" guarantee in
PROJECT_SPEC_1 §86 — is in place from the start.

## Consequences
`app/repositories/evaluation_repository.py` and its ORM models are written during Phase 3
alongside the rest, but are not exercised by any service until Phase 9 wires
`EvaluationService` to them — preserving the execution/evaluation decoupling requirement
(nothing in Phases 3-8 imports from `app/evaluation/`).
