# Scheduled Task Manager

A small, complete, working product: schedule tasks, watch them run, see
their history, and let failed runs retry automatically with exponential
backoff. Built as a 7-day team MVP.

![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20SQLite-blue)

## What it does (MVP scope)

- Create tasks that run on an **interval** (every N seconds) or a **cron** schedule
- Two action types: **HTTP GET** a URL, or run a **mock command** from a
  hardcoded registry (we deliberately never execute arbitrary code)
- A dashboard showing each task and a **live countdown** to its next run
- Full **execution history** per task: every attempt, its status, output, or error
- **Automatic retries** with exponential backoff (30s -> 60s -> 120s -> ...),
  giving up after `max_retries` and moving on to the next scheduled run
- Pause / resume / edit / delete tasks

## Quickstart

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env            # or just use defaults
python seed.py                     # optional but recommended: demo data
uvicorn app.main:app --reload
```
API docs (great for exploring): http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open http://localhost:5173 — set `VITE_USE_MOCK=true` in `frontend/.env`
to run the UI against mock data with no backend (useful on Days 2-3).

### Tests
```bash
cd backend && pytest tests -v
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./scheduler.db` | Use a Supabase/Neon Postgres URL in production |
| `SCHEDULER_TICK_SECONDS` | `15` | How often the scheduler polls for due work |
| `RETRY_BASE_DELAY_SECONDS` | `30` | Base of the backoff formula `base * 2^(attempt-1)` |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origin |
| `API_BASE` | `http://localhost:8000` | Used by `seed.py` for the self health-check task |

## Architecture (one paragraph)

A React dashboard talks to a FastAPI backend. Tasks and their executions
live in one database (SQLite locally, Postgres in production). Inside the
API process a lightweight **polling scheduler** wakes every
`SCHEDULER_TICK_SECONDS`, enqueues due tasks as `queued` executions,
claims them (`queued -> running`), runs the action, and records the
outcome. Failures queue a retry at `now + 30 * 2^(attempt-1)`; after
`max_retries` the execution is `exhausted` and the task's schedule moves
on. All times are stored as naive UTC. Read
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the reasoning behind
each decision.

## Team roles & how to study this repo

| Who | Files to own | Study order |
|---|---|---|
| Scheduler (A) | `backend/app/scheduler.py`, `backend/app/config.py` | 1. `compute_next_run` 2. `backoff_delay` 3. `tick()` 4. `test_scheduler.py` |
| Backend (B) | `backend/app/routers/`, `backend/app/schemas.py`, `backend/app/main.py` | 1. `schemas.py` validators 2. `routers/tasks.py` 3. `test_api.py` |
| Persistence (C) | `backend/app/models.py`, `backend/app/database.py`, `backend/seed.py` | 1. `models.py` 2. `seed.py` 3. run `seed.py`, inspect the DB |
| UI (D) | `frontend/src/` | 1. `api.js` (mock switch) 2. `App.jsx` 3. `Countdown.jsx` 4. rest |
| QA + DevOps (E) | `backend/tests/`, `.github/`, `docs/DEMO_SCRIPT.md` | 1. `test_time_logic.py` 2. run the suite 3. CI workflow |

**Suggested team exercise:** everyone first reads
`docs/ARCHITECTURE.md`, then runs the app + tests, then deletes one file
at a time and rewrites it from scratch.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| POST | `/tasks` | Create task (validated) |
| GET | `/tasks` | List tasks |
| GET | `/tasks/{id}` | One task |
| PATCH | `/tasks/{id}` | Edit / pause / resume |
| DELETE | `/tasks/{id}` | Delete task + its history |
| GET | `/tasks/{id}/executions` | History for one task |
| GET | `/tasks/{id}/next-runs?count=5` | Predicted future runs (demo helper) |
| GET | `/executions?task_id=...` | Global history |

Full contract with JSON examples: [docs/API_CONTRACT.md](docs/API_CONTRACT.md)

## Deployment (free tiers)

1. **DB:** Supabase or Neon free Postgres -> copy the connection URL into `DATABASE_URL`.
2. **Backend:** Render -> new Web Service from this repo, root `backend`,
   build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`,
   add env vars. Note: Render free services sleep when idle; the scheduler
   then simply resumes on the next tick after a request wakes it (a real
   limitation - see below).
3. **Frontend:** Vercel -> import the repo, set root to `frontend`,
   env var `VITE_API_URL` = your Render URL.
4. Update `FRONTEND_URL` on the backend to your Vercel URL (CORS).

## Known limitations (be honest about these at demo time)

- No authentication - single-user product.
- Poll-based scheduling: runs can fire up to `TICK` seconds late; minimum
  practical interval is a few ticks.
- Render free tier sleeps -> scheduler pauses while asleep.
- Resuming a task skips backlogged runs (deliberate, but worth stating).
- Cron schedules are evaluated in the server's UTC; per-timezone cron is v2.
- No Alembic migrations (tables created on startup).
- Frontend uses 30s polling instead of WebSockets.

## If we continued (v2)

Auth & multi-user, real job types, WebSocket live updates, notifications,
metrics dashboard, per-timezone cron, Alembic migrations.

## AI usage

See [AI_USAGE.md](AI_USAGE.md).
