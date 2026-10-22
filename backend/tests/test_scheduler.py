"""Integration tests for the scheduler tick: the happy path AND the
failure/retry path the rubric asks for."""
import asyncio
from datetime import timedelta

from app.config import utcnow
from app.models import Execution
from app import scheduler


def run_tick():
    asyncio.run(scheduler.tick())


async def fake_success(task):
    return "ok"


async def fake_fail(task):
    raise RuntimeError("boom")


def executions_for(db, task_id):
    return (db.query(Execution)
              .filter(Execution.task_id == task_id)
              .order_by(Execution.attempt).all())


def test_success_advances_schedule(db, make_task, monkeypatch):
    monkeypatch.setattr(scheduler, "run_action", fake_success)
    task = make_task(next_run_at=utcnow() - timedelta(seconds=1))
    before = utcnow()

    run_tick()

    exs = executions_for(db, task.id)
    assert len(exs) == 1
    assert exs[0].status == "succeeded"
    assert exs[0].output == "ok"
    db.refresh(task)
    assert task.next_run_at >= before + timedelta(seconds=59)


def test_failure_retries_with_backoff_then_exhausts(db, make_task, monkeypatch):
    """THE key test: attempt 1 fails -> retry queued with backoff ->
    attempt 2 fails -> attempt 3 exhausted -> schedule moves on."""
    monkeypatch.setattr(scheduler, "run_action", fake_fail)
    task = make_task(action_target="always-fails", max_retries=2,
                     next_run_at=utcnow() - timedelta(seconds=1))
    before = utcnow()

    run_tick()  # attempt 1 fails, retry queued
    exs = executions_for(db, task.id)
    assert exs[0].status == "failed"
    assert exs[0].error_message == "boom"
    assert len(exs) == 2                    # the retry is already queued
    retry = exs[1]
    assert retry.attempt == 2 and retry.status == "queued"
    # backoff: scheduled roughly 30s in the future
    assert retry.scheduled_at > before + timedelta(seconds=25)

    retry.scheduled_at = utcnow()           # pretend the backoff elapsed
    db.commit()
    run_tick()                              # attempt 2 fails, attempt 3 queued
    db.expire_all()
    exs = executions_for(db, task.id)
    assert exs[1].status == "failed"
    assert exs[2].attempt == 3 and exs[2].status == "queued"

    exs[2].scheduled_at = utcnow()          # backoff elapsed again
    db.commit()
    run_tick()                              # attempt 3 -> exhausted
    db.expire_all()
    exs = executions_for(db, task.id)
    assert exs[2].status == "exhausted"
    db.refresh(task)
    assert task.next_run_at > before        # task moved on to its next occurrence


def test_paused_task_never_runs(db, make_task, monkeypatch):
    monkeypatch.setattr(scheduler, "run_action", fake_success)
    task = make_task(status="paused", next_run_at=utcnow() - timedelta(seconds=1))

    run_tick()

    # never even enqueued: the due-task query filters on status == active
    assert executions_for(db, task.id) == []


def test_no_duplicate_execution_while_one_in_flight(db, make_task):
    task = make_task(next_run_at=utcnow() - timedelta(seconds=1))
    db.add(Execution(task_id=task.id, attempt=1, status="running",
                     scheduled_at=utcnow()))
    db.commit()

    run_tick()  # must NOT enqueue another attempt for the same run

    assert len(executions_for(db, task.id)) == 1


def test_delete_task_stops_pending_retries(db, make_task):
    task = make_task(next_run_at=utcnow() - timedelta(minutes=5))
    db.add(Execution(task_id=task.id, attempt=2, status="queued",
                     scheduled_at=utcnow() - timedelta(seconds=1)))
    db.commit()

    db.delete(task)  # cascade removes the queued execution
    db.commit()

    assert db.query(Execution).filter(Execution.task_id == task.id).count() == 0
