# ADR-005: Backend package layout follows PROJECT_SPEC_6 §3, not PROJECT_SPEC_1 §20

## Status
Accepted

## Context
PROJECT_SPEC_1 §20 nests `config.py`, `security.py`, `logging.py`, `database.py`, `constants.py`
inside a single `core/` package. PROJECT_SPEC_6 Part 1 §3 ("Core Packages") lists `core/`,
`config/`, `database/` as siblings at the same level, alongside `execution/`, `evaluation/`,
`providers/`, `benchmark/`, `trace/`, `repositories/`, `services/`, `schemas/`, `models/`,
`utils/`.

## Decision
Follow PROJECT_SPEC_6 §3: `app/config/`, `app/database/` are top-level packages beside
`app/core/` (which retains `exceptions.py`, `logging.py`, `constants.py`, `security.py`).
PROJECT_SPEC_6 explicitly states its purpose is "a file-by-file implementation guide that can
be directly translated into production code," making it the more authoritative source for
concrete package boundaries.

## Consequences
Import paths throughout the backend use `app.config.settings`, `app.database.session`, and
`app.core.exceptions` as top-level imports rather than `app.core.config` / `app.core.database`.
