# ADR-003: BaseTool interface is a union of PROJECT_SPEC_1/2 and PROJECT_SPEC_6

## Status
Accepted

## Context
PROJECT_SPEC_1 §30 / PROJECT_SPEC_2 §64 list: `execute, validate_input, schema, metadata, reset,
health_check`. PROJECT_SPEC_6 §47 lists: `name, description, parameters, validate, execute,
serialize_result`.

## Decision
`BaseTool` implements the union: `name`, `description`, `parameters()` (aliasing `schema()`),
`metadata()`, `validate()` (aliasing `validate_input()`), `execute()`, `serialize_result()`,
`reset()`, `health_check()`. Tool implementations remain stateless wherever practical
(PROJECT_SPEC_2 §64).

## Consequences
`ToolRegistry.invoke()` calls `validate()` before `execute()`, then `serialize_result()` before
handing the output to the `TraceRecorder`, satisfying the full tool invocation lifecycle in
PROJECT_SPEC_2 §67 and PROJECT_SPEC_6 §48.
