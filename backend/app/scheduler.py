"""The scheduler engine - the heart of the project and the main thing
you must be able to explain at the demo.

DESIGN DECISION (talk about this!): a cron-style "wake up at exactly
09:00" scheduler is complex to build and deploy. Instead we use a simple
**polling loop**:

    every TICK seconds:
        1. find tasks whose next_run_at <= now  -> enqueue attempt 1
        2. find executions queued with scheduled_at <= now -> claim them
        3. run claimed executions (HTTP call or mock command)
        4. on success: compute the task's next_run_at, move on
        5. on failure: queue a retry at now + backoff(attempt),
           or give up (status=exhausted) if out of retries

Why polling wins for an MVP:
- one deployable unit (no separate worker process)
- missed runs recover automatically (a task due while the server was
  down simply fires on the next tick)
- the "claim" step (queued -> running) prevents double execution
  if two ticks ever overlap

TRADE-OFF (be honest at demo): minimum granularity is TICK seconds,
and a task can fire up to TICK seconds late. Fine for this product.
"""
import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from croniter import croniter

from .config import (
    utcnow, SCHEDULER_TICK_SECONDS, RETRY_BASE_DELAY_SECONDS,
)
from .database import SessionLocal
from .models import Task, Execution

log = logging.getLogger("scheduler")


# ---------- pure time functions (easy to unit test!) ----------

def compute_next_run(task, from_time):
    """When should this task next fire, given a reference time?

    interval: from_time + N seconds
    cron:     next matching instant after from_time (via croniter)
    """
    if task.schedule_type == "interval":
        return from_time + timedelta(seconds=int(task.schedule_value))
    return croniter(task.schedule_value, from_time).get_next(datetime)


def backoff_delay(attempt):
    """Exponential backoff: attempt 1 -> 30s, attempt 2 -> 60s, 3 -> 120s...

    delay = BASE * 2^(attempt-1)
    Longer waits between later retries avoid hammering a struggling service.
    """
    return timedelta(seconds=RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)))


# ---------- the action runner ----------

def _cmd_cleanup():
    return "deleted 3 temp files"


def _cmd_report():
    return "report generated (42 rows)"


def _cmd_fail():
    raise RuntimeError("simulated permanent failure (mock command)")


MOCK_COMMAND_REGISTRY = {
    "cleanup-temp-files": _cmd_cleanup,
    "generate-report": _cmd_report,
    "always-fails": _cmd_fail,
}


async def run_action(task):
    """Execute the task's action and return its output.

    STUDY NOTE on failure handling: we raise on failure rather than
    returning a status code, so tick() can use one try/except for BOTH
    failure types (HTTP error and exception) - see tick().
    """
    if task.action_type == "http":
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(task.action_target)
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.text[:500]
    fn = MOCK_COMMAND_REGISTRY[task.action_target]  # validated at the API layer
    return fn()


# ---------- the tick ----------

async def tick():
    """One scheduler cycle. Written as its own function (not inline in the
    loop) so tests can call it directly and so the loop body is trivial."""
    db = SessionLocal()
    try:
        now = utcnow()

        # -- Step 1: enqueue first attempts for due tasks --
        due_tasks = (
            db.query(Task)
            .filter(Task.status == "active",
                    Task.next_run_at.isnot(None),
                    Task.next_run_at <= now)
            .all()
        )
        for task in due_tasks:
            # Claim guard: never enqueue a second execution while one is
            # already queued/running for this task (prevents double-runs).
            in_flight = db.query(Execution).filter(
                Execution.task_id == task.id,
                Execution.status.in_(["queued", "running"]),
            ).first()
            if in_flight:
                continue
            db.add(Execution(task_id=task.id, attempt=1, status="queued",
                             scheduled_at=task.next_run_at))
        db.commit()

        # -- Step 2: claim due executions (queued -> running) --
        # Only tasks still active may run: pausing a task stops its retries too.
        due = db.query(Execution).filter(
            Execution.status == "queued",
            Execution.scheduled_at <= now,
        ).all()
        for ex in due:
            ex.status = "running"
            ex.started_at = utcnow()
        db.commit()

        # -- Step 3: run each claimed execution --
        for ex in due:
            task = db.get(Task, ex.task_id)
            if task is None:
                continue  # task was deleted between steps
            if task.status != "active":
                ex.status = "failed"
                ex.error_message = "task was paused before this attempt ran"
                ex.finished_at = utcnow()
                db.commit()
                continue

            try:
                output = await run_action(task)
            except Exception as e:                      # ONE handler for all failures
                ex.finished_at = utcnow()
                ex.error_message = str(e)
                if ex.attempt <= task.max_retries:
                    # schedule a retry: next attempt number = attempt + 1
                    ex.status = "failed"
                    retry = Execution(
                        task_id=task.id, attempt=ex.attempt + 1,
                        status="queued", scheduled_at=utcnow() + backoff_delay(ex.attempt),
                    )
                    db.add(retry)
                    log.info("task %s attempt %d failed, retry %d scheduled",
                             task.name, ex.attempt, retry.attempt)
                else:
                    # out of retries. We advanced next_run_at anyway so the
                    # task moves on to its NEXT scheduled occurrence.
                    ex.status = "exhausted"
                    task.next_run_at = compute_next_run(task, utcnow())
                    log.warning("task %s exhausted retries", task.name)
            else:
                ex.status = "succeeded"
                ex.output = output
                ex.finished_at = utcnow()
                task.next_run_at = compute_next_run(task, utcnow())
            db.commit()
    finally:
        db.close()


async def scheduler_loop():
    """Runs forever inside the FastAPI process. try/except inside the loop
    means one bad tick can never kill the scheduler."""
    log.info("scheduler started (tick every %ss)", SCHEDULER_TICK_SECONDS)
    while True:
        try:
            await tick()
        except Exception:
            log.exception("scheduler tick failed")
        await asyncio.sleep(SCHEDULER_TICK_SECONDS)

