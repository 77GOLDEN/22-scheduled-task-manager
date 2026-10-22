"""Shared test setup.

IMPORTANT: environment variables MUST be set BEFORE importing any
app.* module, because config.py reads them at import time.
"""
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/test.db"
os.environ["SCHEDULER_TICK_SECONDS"] = "3600"  # stop the background loop from interfering

import pytest
from app.database import Base, engine, SessionLocal
from app.models import Task, Execution


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def make_task(db):
    """Factory: make_task(name=..., action_target=..., ...) -> Task persisted."""
    import uuid
    from app.config import utcnow

    def _make(**overrides):
        defaults = dict(
            id=uuid.uuid4(),
            name="test task",
            action_type="mock_command",
            action_target="cleanup-temp-files",
            schedule_type="interval",
            schedule_value="60",
            max_retries=2,
            status="active",
            next_run_at=utcnow(),
        )
        task = Task(**{**defaults, **overrides})
        db.add(task)
        db.commit()
        return task
    return _make
