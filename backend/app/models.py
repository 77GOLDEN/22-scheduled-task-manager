"""SQLAlchemy ORM models = the database tables.

STUDY NOTE: models.py defines STRUCTURE, schemas.py defines VALIDATION.
Keep them separate - a classic beginner mistake is mixing the two.
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from .database import Base
from .config import utcnow


class Task(Base):
    """A schedulable unit of work."""
    __tablename__ = "tasks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    # "http"          -> we make an HTTP GET request to action_target
    # "mock_command"  -> we call a hardcoded function from the registry.
    #                    We NEVER execute arbitrary shell code (security rule).
    action_type = Column(String(20), nullable=False)
    action_target = Column(String(500), nullable=False)      # URL or registry key
    schedule_type = Column(String(20), nullable=False)       # "interval" | "cron"
    schedule_value = Column(String(120), nullable=False)     # seconds or cron expr
    timezone = Column(String(64), nullable=False, default="UTC")
    max_retries = Column(Integer, nullable=False, default=3)
    status = Column(String(20), nullable=False, default="active")  # active | paused

    # When the task should next fire. Computed and stored (not re-derived
    # each tick) so the scheduler query stays a trivial indexed lookup.
    next_run_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    executions = relationship(
        "Execution", back_populates="task",
        cascade="all, delete-orphan",           # deleting a task deletes its history
        order_by="desc(Execution.scheduled_at)",
    )


class Execution(Base):
    """One attempt of one task. A task run may produce several executions
    (attempt 1, retry attempt 2, ...). This history is what the dashboard shows.

    Status lifecycle:
        queued  -> waiting for scheduled_at (first attempt OR a retry)
        running -> claimed by the scheduler, action is executing
        succeeded
        failed  -> this attempt failed, a retry may be queued
        exhausted -> this attempt failed and no retries remain
    """
    __tablename__ = "executions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    task_id = Column(Uuid, ForeignKey("tasks.id"), nullable=False, index=True)
    attempt = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    scheduled_at = Column(DateTime, nullable=False)   # when this attempt should run
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    output = Column(Text, nullable=True)

    task = relationship("Task", back_populates="executions")
