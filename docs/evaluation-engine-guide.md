# Evaluation Engine Guide

## Adding a new evaluator

Per PROJECT_SPEC_3 §27, adding an evaluator requires a new evaluator class, a rubric definition,
and registration -- no changes to any existing evaluator.

1. Add a rubric entry to `backend/app/evaluation/rubric/definitions.py`'s `RUBRICS` dict (reuse
   `_STANDARD_LEVELS` for the five-level scale unless you have a specific reason not to).
2. Create `backend/app/evaluation/evaluators/<name>.py`, subclassing `BaseEvaluator`
   (`app/evaluation/evaluators/base.py`). Set `name`, `description`, `evidence_categories`
   (see `EvidenceExtractor.extract()` for the supported category list), and implement
   `evaluator_instructions()` -- a short paragraph telling the Judge exactly what this evaluator
   does and does not judge.
3. Register it in `build_default_registry()` (`app/evaluation/evaluators/registry.py`), in the
   position matching PROJECT_SPEC_3 §8's evaluation sequence.
4. Add the evaluator's name to `app.core.constants.EVALUATOR_NAMES` and give it a weight in
   `app/evaluation/scoring/cts.py`'s `DEFAULT_WEIGHTS` (all weights must still sum to 1.0).
5. Add tests: one in `backend/tests/unit/evaluation/test_evaluators.py`'s parametrized
   `ALL_EVALUATOR_CLASSES` list, plus rubric coverage in `test_rubric.py`.

## How scoring works end to end

`BaseEvaluator.evaluate()` is a template method: `validate()` -> `extract_evidence()` -> build a
Judge prompt from the rubric + evidence -> `JudgeService.submit()` -> `validate_response()` ->
`generate_reasoning()` / `compute_confidence()` -> assemble an `EvaluationResult` (score 0-10,
confidence 0.0-1.0). `EvaluatorRegistry.run_all()` runs every evaluator concurrently via
`asyncio.gather` since none depends on another's output.

`CTSCalculator.compute()` then normalizes and weights every score, applies hard caps for critical
security/tool-faithfulness/integrity failures, and produces the Composite Trust Score.
`BehaviourClassifier` and `FailureAttributionEngine` run independently of CTS, from the same ten
results.

See `docs/adr/0008-evaluation-engine-reconciliations.md` for why the evaluator names and
`BaseEvaluator` interface look the way they do relative to the individual spec documents.
