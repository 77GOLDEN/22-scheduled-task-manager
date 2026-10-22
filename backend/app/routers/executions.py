"""Read-only endpoints for the global execution history."""
from fastapi import APIRouter, Depends
from uuid import UUID
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Execution
from ..schemas import ExecutionOut

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionOut])
def list_executions(task_id: UUID | None = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Execution)
    if task_id:
        q = q.filter(Execution.task_id == task_id)
    return q.order_by(Execution.scheduled_at.desc()).limit(min(limit, 200)).all()
