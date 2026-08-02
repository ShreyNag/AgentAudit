# ADR-004: BaseEnvironment interface is a union of PROJECT_SPEC_2 and PROJECT_SPEC_6

## Status
Accepted

## Context
PROJECT_SPEC_2 §59 lists: `initialize, reset, get_state, apply_action, validate_action,
export_state, cleanup`. PROJECT_SPEC_6 §50 lists: `initialize, reset, observe, step,
is_complete, cleanup`.

## Decision
`BaseEnvironment` implements the union: `initialize()`, `reset()`, `observe()` (aliasing
`get_state()`), `step()` (aliasing `apply_action()`), `validate_action()`, `is_complete()`,
`export_state()`, `cleanup()`. Every concrete environment (Banking, Payments, Marketplace,
Trip Planner, Email, Identity Documents, Jailbreak, Memory Poisoning) implements this full
interface with isolated, in-memory, deterministically-seeded state per PROJECT_SPEC_1 §56/§61.

## Consequences
The `ExecutionRunner` interacts with environments only through this interface, and only tools
call into it — the AUT never receives direct environment access (PROJECT_SPEC_1 §55),
preserving ground-truth isolation.
