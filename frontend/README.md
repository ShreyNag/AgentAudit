# AgentAudit Frontend

React 18 + TypeScript + Vite dashboard, trace viewer, evaluation report UI, and analytics for
AgentAudit (PROJECT_SPEC_4).

## Quick Start

```bash
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your running backend
npm run dev
```

## Layout

```
src/
├── api/            Axios client + one service module per backend resource
├── components/     Shared UI primitives (Button, Card, Badge, Table, ...) and layout chrome
├── context/         Theme and sidebar state (no execution data lives here)
├── features/        Feature-scoped components (benchmark launcher, trace timeline, evaluation)
├── hooks/            React Query hooks, one per resource
├── layouts/          MainLayout: sidebar + header + page outlet
├── lib/              Formatting helpers and the `cn` class-name utility
├── pages/            Route-level components (lazy-loaded)
├── styles/           Tailwind entrypoint
└── types/            TypeScript models mirroring backend response schemas
```

## Scope notes

A few things described in PROJECT_SPEC_4 were deliberately scoped down for this build, since this
environment has no Node.js/browser to validate a heavier implementation against:

- No shadcn/ui CLI-generated component set; a small hand-built Tailwind component library
  (`components/ui/`) covers the same surface (Button, Card, Badge, Table, Dialog, Skeleton,
  Alert, EmptyState, ErrorState, JsonViewer).
- The Trace Viewer's Replay mode presents the persisted, immutably-ordered timeline directly
  rather than an animated play/pause/speed-controlled player -- the underlying data and ordering
  guarantees are identical either way.
- The Analytics page renders the point-in-time aggregates the backend actually exposes
  (provider/environment/evaluator breakdowns); time-bucketed historical trend charts would need
  an additional backend endpoint that wasn't built in this pass.

## Testing

```bash
npm run test        # vitest + @testing-library/react
npm run typecheck    # tsc --noEmit
npm run lint
```
