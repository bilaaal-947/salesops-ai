# SalesOps AI

Autonomous AI Sales Operations Agent — see `docs/architecture/` for the full system design.

## Status: Phase 1 — Project Foundation (in progress)

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

Then check:
- `http://localhost:8000/health` — backend + DB connectivity
- `http://localhost:8000/docs` — auto-generated API docs

## Structure

- `backend/` — FastAPI + LangGraph agent + Celery workers
- `frontend/` — Next.js dashboard
- `n8n/workflows/` — scheduled/webhook automation
- `docs/` — architecture, ADRs, API docs
- `evaluations/` — agent benchmark dataset and results
