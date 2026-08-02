# ADR-006: Alembic lives at backend/alembic/, not backend/app/migrations/

## Status
Accepted

## Context
PROJECT_SPEC_1 §20 shows `migrations/` nested under `backend/app/`. In practice, Alembic's own
`alembic init` scaffolding (env.py, script.py.mako, versions/) is designed to sit beside the
application package, not inside it, and fighting that convention adds friction with no
architectural benefit — PROJECT_SPEC_1's dependency rules only require that migrations be
generated from `app/models/` and applied via Alembic (§94), not that the directory be nested in
a specific place.

## Decision
Alembic configuration lives at `backend/alembic.ini` and `backend/alembic/` (env.py,
script.py.mako, `versions/`). `app/models/` remains the single source of ORM metadata that
`alembic revision --autogenerate` reads from, via `target_metadata = Base.metadata` imported
from `app.database.base`.

## Consequences
Running migrations is `cd backend && alembic upgrade head`, independent of how `app/` is
packaged or installed.
