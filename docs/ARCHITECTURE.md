# Architecture decisions and WHY (study this file first)

Every heading here is a demo talking point. If you can explain each of
these, you can explain the whole project.

## 1. Polling scheduler instead of cron-style exact-time triggers

The scheduler is an async loop inside the FastAPI process. Every
`SCHEDULER_TICK_SECONDS` it calls `tick()`, which:

1. finds `active` tasks with `next_run_at <= now` and enqueues an
   `Execution(attempt=1, status="queued")` for them
2. claims due queued executions by flipping them to `running`
3. awaits the action (HTTP GET or mock command)
4. on success: records output, advances `task.next_run_at`
5. on failure: queues a retry at `now + backoff(attempt)`, or marks the
   execution `exhausted` if out of retries

**Why polling wins for a 7-day MVP:**
- One deployable unit - no separate worker process to provision.
- Self-healing: a task that came due while the server was down just fires
  on the next tick. With exact-time triggers you'd need catch-up logic.
- The claim step (`queued -> running`) prevents double execution if two
  ticks ever overlap.

**The trade-off (say this at the demo):** granularity is limited to the
tick length, and runs can be up to `TICK` seconds late. For this product
that is fine; for "invoice must fire at 00:00:00 sharp" you would need a
different design.

## 2. All times are naive UTC

`config.utcnow()` returns `datetime.now(timezone.utc).replace(tzinfo=None)`.
Every datetime written to or read from the DB is naive UTC. The frontend
appends `"Z"` before parsing (`new Date(iso + "Z")`) so browsers render it
in the user's local timezone.

**Why:** mixing timezone-aware and naive datetimes raises
`TypeError: can't compare offset-naive and offset-aware` at the worst
possible moment. One rule, one helper, no surprises. The limitation:
cron expressions are evaluated in UTC regardless of the `timezone` field
(stored for v2 per-timezone support).

## 3. Retry design

- `max_retries` means retries AFTER the first attempt (total attempts =
  `1 + max_retries`). This is stated in the README to avoid confusion.
- Backoff: `delay = RETRY_BASE_DELAY_SECONDS * 2^(attempt-1)`
  (30s, 60s, 120s, ...). Exponential backoff avoids hammering a service
  that is already struggling.
- Retries are just more rows in the `executions` table with
  `status="queued"` and a future `scheduled_at`. Step 2 of `tick()` picks
  them up exactly like first attempts - one mechanism, two sources.
- When retries run out, the execution is `exhausted` and the TASK's
  `next_run_at` still advances, so one bad run never blocks the schedule.

## 4. The claim mechanism (no double runs)

Two things protect against duplicate execution:
- Step 1 skips enqueuing if the task already has a `queued` or `running`
  execution (test: `test_no_duplicate_execution_while_one_in_flight`).
- Step 2's `queued -> running` transition is a single commit, so two
  overlapping ticks can't claim the same execution.

## 5. Never execute arbitrary code

Actions are only ever `http` (GET to a validated URL) or a key into a
hardcoded `MOCK_COMMAND_REGISTRY`. User input is validated to match one
of these exactly - the API test literally tries `"rm -rf /"` and expects
a 422. This is both a rubric point (safe handling of constraints) and a
real security boundary.

## 6. SQLite locally, Postgres in production

Same SQLAlchemy code runs on both; `DATABASE_URL` switches the backend.
SQLite gives zero-setup development (a file, no server). Postgres is what
the free Supabase/Neon tiers provide for deployment. Trade-off: we lose
Postgres-specific features and can't rely on `SELECT ... FOR UPDATE`
(we use status transitions instead - which works on both).

## 7. Why executions are separate rows (not a counter on the task)

History is a first-class feature: the dashboard shows every attempt with
its error/output. Storing each attempt as a row makes retries, the
`exhausted` state, and the UI's history view trivial - and costs nothing
at this scale.

## 8. Deliberate simplifications (each one is a fair exam question)

- `create_all()` on startup instead of Alembic migrations.
- CORS pinned to one origin, no auth.
- Pausing then resuming recomputes from `now` (skips backlogged runs).
- `PATCH` validation re-implemented in the router instead of reusing the
  `TaskCreate` validator (partial updates don't fit its assumptions).
