# AgentAudit Architecture Guide

## Layers

```
Frontend (React)
      │ REST (Axios)
      ▼
FastAPI (app/api)
      │
      ▼
Services (app/services)         <- all business logic lives here
      │              │
      ▼              ▼
Execution Engine   Evaluation Engine     <- fully decoupled, no cross-imports
      │              │
      ▼              ▼
Repositories (app/repositories)
      │
      ▼
MySQL
```

Execution and Evaluation are architecturally independent: nothing in `app/execution`,
`app/environments`, or `app/tools` imports from `app/evaluation`, and vice versa. Evaluation only
ever reads a persisted `ExecutionTrace` (via `execution_traces.trace_json`); it never touches a
provider except through the Judge, never calls a benchmark tool, and never re-runs the AUT.

## Request lifecycle (launch -> execute -> persist)

1. `POST /api/v1/benchmarks/run` -> `ExecutionService.launch()`
2. Loads the task, validates it (`BenchmarkValidator`), resolves the AUT provider
   (`ProviderFactory`)
3. `ExecutionRunner` resolves the environment + tools, builds an `ExecutionContext`, and hands off
   to `CommonAgentExecutor`
4. `CommonAgentExecutor` runs the tool-calling reasoning loop, recording every step through
   `TraceRecorder`
5. `ExecutionService` persists the `Run`, `ExecutionTrace`, `TraceEvent`s, `ToolCall`s, and
   `ToolOutput`s -- all before returning

## Request lifecycle (evaluate)

1. `POST /api/v1/runs/{id}/evaluate` -> `EvaluationService.evaluate_run()`
2. Loads the persisted trace (`ExecutionTrace.model_validate(trace_json)`) and builds an
   `EvaluationContext`
3. `EvaluationEngine` runs all ten evaluators concurrently (`EvaluatorRegistry`, each backed by
   `JudgeService`), then `BehaviourClassifier`, `FailureAttributionEngine`, and `CTSCalculator`
4. `EvaluationService` persists the `EvaluationReport`, ten `EvaluationScore` rows,
   `BehaviourReport`, and (if applicable) `FailureReport`

Re-running step 1 against a historical run re-evaluates it without touching the execution side at
all.

## Provider abstraction

Every LLM call -- AUT or Judge -- goes through `BaseProvider` (`app/providers/base.py`),
constructed by `ProviderFactory`. Concrete adapters exist for OpenAI, Anthropic, Gemini,
DeepSeek, Groq, and Ollama. See `provider-integration-guide.md` to add a new one.

## Benchmark environments

Each environment (`app/environments/<name>/`) owns its own state, tools, and one seed task. See
`environment-authoring-guide.md` to add a new one.

## Reconciliations

Where the six specification documents were ambiguous or in tension, the decision and reasoning
is recorded in `docs/adr/`.
