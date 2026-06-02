# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

HR Partner — a personal job monitoring agent. It runs daily, searches Google Jobs via SerpAPI using configurable queries, scores each listing with Claude (Sonnet 4.6), and emails a digest of relevant jobs. It also adapts the user's resume to specific job descriptions on demand.

## Commands

```bash
# Run locally
uvicorn app.main:app --reload

# Run tests
pytest

# Run single test
pytest tests/test_pipeline.py::test_name -v

# Install deps
pip install -r requirements.txt
```

## Architecture

**Entry point**: `app/main.py` — FastAPI app with APScheduler wired via `lifespan`.

**Pipeline** (`app/pipeline.py`): The core flow, runs daily at 08:00 Europe/Paris or on `POST /run`:
1. Fetch active search queries from SQLite
2. Call SerpAPI → raw job list (`app/search.py`)
3. Deduplicate against seen job IDs in DB
4. Score each new job with Claude (`app/relevance.py`) — uses prompt caching on system prompt
5. Save all scored jobs to DB; email digest for jobs above `MIN_SCORE`

**Storage** (`app/storage.py`): aiosqlite wrapper. Three tables: `jobs`, `search_queries`, `adapted_resumes`. DB path is configurable via env (`DATABASE_PATH`, default `/data/jobs.db`).

**Resume adaptation** (`app/resume.py`): Blocking Claude call, run in thread pool via `run_in_executor` to avoid blocking the async event loop. Adapted resumes are cached in DB.

**Scoring** (`app/relevance.py`): Calls Claude per job with prompt caching on `USER_PROFILE` system prompt. Falls back gracefully (score=0) on parse/API errors.

**Config** (`app/config.py`): Pydantic Settings, reads from `.env` or env vars.

## Key Env Vars

| Var | Purpose |
|-----|---------|
| `SERPAPI_KEY` | Google Jobs search |
| `ANTHROPIC_API_KEY` | Job scoring + resume adaptation |
| `SENDGRID_API_KEY` | Email digests |
| `EMAIL_TO` / `EMAIL_FROM` | Digest recipients |
| `RUN_TOKEN` | Bearer token for `POST /run` |
| `MIN_SCORE` | Relevance threshold (default 60) |
| `DATABASE_PATH` | SQLite path (default `/data/jobs.db`) |
| `RESUME_PATH` | Resume file path (default `/data/resume.md`) |

Copy `.env.example` to `.env` for local dev.

## Deployment

Render.com via `render.yaml`. Requires a 1GB persistent disk mounted at `/data` for SQLite and resume file. Push to `main` to trigger deploy.

See `DEPLOY.md` for full Render setup steps.
