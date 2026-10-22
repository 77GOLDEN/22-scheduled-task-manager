"""Task CRUD endpoints."""
import logging
from datetime import datetime
from uuid import UUID

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import utcnow, MIN_INTERVAL_SECONDS
from ..database import get_db
from ..models import Task, Execution
from ..scheduler import compute_next_run
from ..schemas import TaskCreate, TaskUpdate, TaskOut, ExecutionOut

log = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _validate_update(payload: TaskUpdate):
    """Validates partial updates. Shares the same RULES as TaskCreate but
    must handle 'only one schedule field sent' - so we can't reuse the
    pydantic validator directly. Document this as a known simplification."""
    if payload.schedule_type == "interval" and payload.schedule_value is not None:
        try:
            if int(payload.schedule_value) < MIN_INTERVAL_SECONDS:
                raise HTTPException(422, f"interval must be >= {MIN_INTERVAL_SECONDS}s")
        except ValueError:
            raise HTTPException(422, "interval schedule_value must be an integer")
    if payload.schedule_type == "cron" and payload.schedule_value is not None:
        if not croniter.is_valid(payload.schedule_value):
            raise HTTPException(422, "invalid cron expression")


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    task.next_run_at = compute_next_run(task, utcnow())
    db.add(task)
    db.commit()
    db.refresh(task)
    log.info("created task %s", task.name)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "task not found")

    _validate_update(payload)

    changes = payload.model_dump(exclude_unset=True)
    was_paused = task.status == "paused"
    for key, value in changes.items():
        setattr(task, key, value)

    # If the schedule changed, or the task was just resumed, recompute
    # next_run_at from NOW (never fire "backlogged" runs - deliberate choice).
    schedule_changed = "schedule_type" in changes or "schedule_value" in changes
    just_resumed = was_paused and task.status == "active"
    if schedule_changed or just_resumed:
        task.next_run_at = compute_next_run(task, utcnow())

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "task not found")
    db.delete(task)  # executions cascade (see models.py relationship)
    db.commit()


@router.get("/{task_id}/executions", response_model=list[ExecutionOut])
def task_executions(task_id: UUID, db: Session = Depends(get_db)):
    if db.get(Task, task_id) is None:
        raise HTTPException(404, "task not found")
    return (db.query(Execution)
              .filter(Execution.task_id == task_id)
              .order_by(Execution.scheduled_at.desc())
              .limit(50).all())


@router.get("/{task_id}/next-runs", response_model=list[datetime])
def next_runs(task_id: UUID, count: int = 5, db: Session = Depends(get_db)):
    """Demo helper: the next N predicted run times, computed from
    max(next_run_at, now). Read-only; never affects the schedule."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "task not found")
    start = task.next_run_at if task.next_run_at and task.next_run_at > utcnow() else utcnow()
    runs, cursor = [], start
    for _ in range(min(count, 20)):
        cursor = compute_next_run(task, cursor)
        runs.append(cursor)
    return runs
