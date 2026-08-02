# ADR-002: BaseProvider interface is a union of PROJECT_SPEC_2 and PROJECT_SPEC_6

## Status
Accepted

## Context
PROJECT_SPEC_2 §30 lists the provider interface as: `generate, chat, stream, reason,
health_check, list_models, count_tokens, estimate_cost, close`.

PROJECT_SPEC_6 §43 ("Provider Adapter Interface") lists: `initialize, generate, stream_generate,
count_tokens, validate_configuration, shutdown`.

These are not contradictory — PROJECT_SPEC_6's list is a tighter subset focused on the
execution-loop's hot path, while PROJECT_SPEC_2's list covers operational/reporting concerns
(`health_check`, `list_models`, `estimate_cost`) required elsewhere by acceptance criteria
(PROJECT_SPEC_2 §50) and by REST endpoints (`GET /api/v1/providers/health`,
`GET /api/v1/providers/models`).

## Decision
`BaseProvider` implements the full union of both lists:

```
initialize()          validate_configuration()
generate()             chat()
stream()  (alias for stream_generate())
reason()
count_tokens()
estimate_cost()
health_check()
list_models()
shutdown()  (alias exposed as close() for call-site ergonomics)
```

No method from either specification is dropped.

## Consequences
Every concrete adapter (OpenAI, Anthropic, Gemini, DeepSeek, Groq, Ollama) must implement the
full interface; adapters for providers without a given capability (e.g. no native `reason()`
step, no cost data) return a structured "unsupported" result rather than raising, per
PROJECT_SPEC_2 §45.
