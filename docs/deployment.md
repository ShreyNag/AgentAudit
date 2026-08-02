# Deployment Guide

## Local development (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp ../.env.example ../.env   # fill in AUT_API_KEY / JUDGE_API_KEY
alembic upgrade head
uvicorn app.main:app --reload

cd ../frontend
npm install
cp .env.example .env
npm run dev
```

## Docker Compose

```bash
cp .env.example .env   # fill in AUT_API_KEY / JUDGE_API_KEY at minimum
docker compose up --build
```

This starts three services:

- `mysql` — MySQL 8, with a named volume for persistence
- `backend` — runs `alembic upgrade head` then `uvicorn`, on port 8000
- `frontend` — the Vite production build served by nginx, on port 5173 (nginx proxies `/api/*`
  to the `backend` service, so the frontend needs no separate CORS configuration in this mode)

## Production notes

- Set `DEBUG=false` and a real, random `SECRET_KEY`.
- Set `MYSQL_PASSWORD` to a strong, unique value (the compose file's default is for local
  development only).
- `AUT_API_KEY` / `JUDGE_API_KEY` / `MYSQL_PASSWORD` must only ever be provided via environment
  variables (or your platform's secret manager) -- never committed, never stored in the
  database (PROJECT_SPEC_1 §101).
- Run `alembic upgrade head` as part of your deployment pipeline before starting new backend
  instances, not automatically on every container start in a multi-replica setup (the
  docker-compose command here is convenient for a single-instance deployment, not a
  multi-replica one).
