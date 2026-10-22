"""Pydantic schemas: validation in, serialisation out.

STUDY NOTES
-----------
- TaskCreate  = what the client may SEND us (strictly validated)
- TaskUpdate  = partial updates; all fields optional
- TaskOut / ExecutionOut = what we RETURN (never leak internals we don't want shown)
- The validators below are your "validation" rubric points. Be able to
  explain each one at the demo.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from croniter import croniter

# Hardcoded registry of fake commands. Deterministic, safe, offline-friendly.
# In v2 these could be real registered jobs (see ARCHITECTURE.md).
MOCK_COMMANDS = ["cleanup-temp-files", "generate-report", "always-fails"]


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    action_type: Literal["http", "mock_command"]
    action_target: str = Field(min_length=1, max_length=500)
    schedule_type: Literal["interval", "cron"]
    schedule_value: str = Field(min_length=1, max_length=120)
    timezone: str = Field(default="UTC", max_length=64)
    max_retries: int = Field(default=3, ge=0, le=10)

    @field_validator("action_target")
    @classmethod
    def target_must_match_type(cls, v, info):
        action_type = info.data.get("action_type")
        if action_type == "http" and not v.startswith(("http://", "https://")):
            raise ValueError("action_target must be a URL starting with http:// or https://")
        if action_type == "mock_command" and v not in MOCK_COMMANDS:
            raise ValueError(f"unknown mock command, choose from: {MOCK_COMMANDS}")
        return v

    @field_validator("schedule_value")
    @classmethod
    def schedule_must_be_valid(cls, v, info):
        schedule_type = info.data.get("schedule_type")
        if schedule_type == "interval":
            try:
                seconds = int(v)
            except ValueError:
                raise ValueError("interval schedule_value must be an integer number of seconds")
            if seconds < 10:
                raise ValueError("interval must be at least 10 seconds")
        elif schedule_type == "cron":
            if not croniter.is_valid(v):
                raise ValueError("invalid cron expression (5 fields, e.g. '0 9 * * *')")
        return v


class TaskUpdate(BaseModel):
    """All fields optional - only send what you want to change."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    schedule_type: Optional[Literal["interval", "cron"]] = None
    schedule_value: Optional[str] = Field(default=None, min_length=1, max_length=120)
    timezone: Optional[str] = Field(default=None, max_length=64)
    max_retries: Optional[int] = Field(default=None, ge=0, le=10)
    status: Optional[Literal["active", "paused"]] = None  # pause/resume


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    action_type: str
    action_target: str
    schedule_type: str
    schedule_value: str
    timezone: str
    max_retries: int
    status: str
    next_run_at: Optional[datetime]
    created_at: datetime


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    attempt: int
    status: str
    scheduled_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    output: Optional[str]
