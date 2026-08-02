# AgentAudit Backend

FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2 implementation of the AgentAudit execution and
evaluation engines. See the repository root `README.md` for quick start instructions and
`docs/` for architecture documentation and ADRs.

## Layout

```
app/
├── api/            FastAPI routers, request/response schemas, dependency providers
├── core/           Exceptions, logging, constants
├── config/         Pydantic Settings (environment-driven configuration)
├── database/       Async engine/session management, declarative base
├── models/         SQLAlchemy ORM models (14 tables)
├── schemas/        Pydantic API schemas (independent from ORM models)
├── repositories/   Persistence-only CRUD/query classes
├── services/       Business workflows (compose repositories + engines)
├── providers/      Provider-agnostic LLM abstraction (BaseProvider + 6 adapters)
├── benchmark/      Benchmark/Task registry, loader, validator
├── environments/   BaseEnvironment + 7 concrete benchmark environments
├── tools/          BaseTool, ToolRegistry, concrete tool implementations
├── execution/      CommonAgentExecutor, ExecutionContext/State/Config/Result, Planner, Runner
├── trace/          TraceRecorder, event types, serializer, replay loader
├── evaluation/     EvaluationEngine, 10 evaluators, Judge, rubrics, CTS, behaviour/failure
├── utils/          Shared, dependency-free helpers
└── main.py         Application factory
```

Dependency direction is strictly inward: `api -> services -> {execution|evaluation} ->
repositories -> database`. See `docs/adr/0001-*.md` through `0007-*.md` for reconciliations
made where the specification documents were ambiguous or in tension with each other.
