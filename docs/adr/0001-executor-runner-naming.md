# ADR-001: CommonAgentExecutor vs Runner naming

## Status
Accepted

## Context
PROJECT_SPEC_1 §33/§48 and PROJECT_SPEC_2 §49/§69-72 describe a `Runner` that orchestrates an
entire benchmark execution (load task, load provider, load environment, initialize tools,
execute agent, capture events, persist trace), sitting above a `CommonAgentExecutor` whose sole
job is normalized LLM I/O (`Runner → CommonAgentExecutor → Provider Adapter → LLM`).

PROJECT_SPEC_6 Part 2 §35-36 redefines `CommonAgentExecutor` as the orchestration entry point
itself: "the orchestration entry point for every benchmark execution," responsible for
initializing context, loading the benchmark, resolving the provider, registering tools,
executing the reasoning loop, capturing trace events, and persisting execution state — i.e. the
full `Runner` responsibility list from the earlier specs, under a different class name.

## Decision
PROJECT_SPEC_6 is the later, concrete, file-by-file implementation authority, so its naming
wins:

- `CommonAgentExecutor` = the orchestrator: owns the reasoning loop and coordinates
  `ExecutionPlanner`, the provider adapter, `ToolRegistry`, and `TraceRecorder`.
- The per-vendor LLM I/O normalizer (what PROJECT_SPEC_2 originally called
  `CommonAgentExecutor`) is implemented as `BaseProvider` / concrete provider adapters, matching
  PROJECT_SPEC_6 §43's own term "Provider Adapter Interface."
- A thin `ExecutionRunner` (`app/execution/runner.py`) is kept as the service-facing entry point
  that resolves the task, environment, provider, and tools, builds the `ExecutionContext`, and
  hands off to `CommonAgentExecutor` — this preserves PROJECT_SPEC_1/2's documented "Runner
  responsibilities" list without a class-name collision with PROJECT_SPEC_6.

## Consequences
Code and diagrams in this repository use `CommonAgentExecutor` exactly as PROJECT_SPEC_6
describes it. Readers cross-referencing PROJECT_SPEC_1/2's `Runner` section should map that
responsibility list onto `ExecutionRunner` + `CommonAgentExecutor` together.
