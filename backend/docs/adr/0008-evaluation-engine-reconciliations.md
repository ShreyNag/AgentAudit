# ADR-008: Evaluation Engine reconciliations (evaluator names, BaseEvaluator, Judge routing)

## Status
Accepted

## Context
Three separate tensions surfaced between specification documents while implementing Phase 9:

1. **Evaluator names.** PROJECT_SPEC_1 SS2 (vision doc, Principle 2) lists the ten evaluation
   dimensions loosely as "...Grounding, Security, Behaviour, Integrity." PROJECT_SPEC_2 SS86 and
   PROJECT_SPEC_3 SS30/SS78/SS91 (the detailed Evaluation Engine spec, three independent times)
   both give the precise list: Instruction Integrity, Planner, Memory, Tool Selection, Tool
   Invocation, Tool Correctness, **Alignment**, **Tool Faithfulness**, Security, Integrity.

2. **BaseEvaluator interface.** PROJECT_SPEC_3 SS10 lists internal workflow steps (`evaluate,
   validate, extract_evidence, generate_reasoning, compute_confidence, metadata`).
   PROJECT_SPEC_6 SS69 lists a discovery/identity interface (`name, description, version,
   evaluate(context), supported_trace_versions, required_events`).

3. **Judge routing.** PROJECT_SPEC_3 SS21 draws `Evaluation Engine -> Judge Service -> Common
   Agent Executor -> Judge Provider -> LLM`. Per ADR-001, `CommonAgentExecutor` is specifically
   the AUT's tool-calling reasoning-loop orchestrator (bound to a benchmark environment and
   tool registry) -- routing a single-shot Judge prompt through it would be a category error.

## Decision
1. Evaluator names follow PROJECT_SPEC_3 (repeated three times, and consistent with
   PROJECT_SPEC_2 SS86's DB-facing examples) since it is the specification explicitly and
   repeatedly dedicated to this subsystem: `instruction_integrity, planner, memory,
   tool_selection, tool_invocation, tool_correctness, alignment, tool_faithfulness, security,
   integrity`. `app.core.constants.EVALUATOR_NAMES` reflects this list.
2. `BaseEvaluator` merges both interfaces: `name`, `description`, `version`,
   `supported_trace_versions()`, `required_events()` are identity/discovery metadata (PROJECT_
   SPEC_6); `evaluate(context)` is a template method whose internal steps are exactly PROJECT_
   SPEC_3's workflow (`validate` -> `extract_evidence` -> build prompt -> invoke Judge ->
   `generate_reasoning` / `compute_confidence` -> assemble `EvaluationResult`). Concrete
   evaluators override `extract_evidence()` and `evaluator_instructions()` only.
3. `JudgeService` invokes the Judge's `BaseProvider` adapter directly (via
   `ProviderFactory.create_judge`) -- the same provider abstraction the AUT uses (PROJECT_SPEC_1
   SS12/SS48), but without a `CommonAgentExecutor`/tool-loop/environment in between, since a
   Judge call is a single-shot structured-output request, not a multi-turn tool-calling episode.

## Consequences
`evaluation_scores.evaluator_name` values in the database are exactly the ten names above.
Score scale is 0-10 (PROJECT_SPEC_3 SS14/SS42), confidence scale is 0.0-1.0 (PROJECT_SPEC_3
SS18/SS69), matching the `EvaluationScoreModel.score`/`confidence` columns already created in
Phase 3.
