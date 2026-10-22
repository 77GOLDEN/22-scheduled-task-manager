"""One-command demo data:  python seed.py   (from inside backend/)

Idempotent: wipes and re-creates the tables. Gives you a dashboard that
already looks alive the moment you open the frontend.
"""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import utcnow
from app.database import Base, engine, SessionLocal
from app.models import Task, Execution
from app.scheduler import compute_next_run

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

now = utcnow()

tasks = [
    Task(name="Self health check",
         action_type="http", action_target=f"{API_BASE}/health",
         schedule_type="interval", schedule_value="300",
         max_retries=1, next_run_at=now + timedelta(seconds=300)),
    Task(name="Cleanup temp files",
         action_type="mock_command", action_target="cleanup-temp-files",
         schedule_type="interval", schedule_value="3600",
         max_retries=3, next_run_at=now + timedelta(seconds=3600)),
    Task(name="Generate morning report",
         action_type="mock_command", action_target="generate-report",
         schedule_type="cron", schedule_value="0 9 * * *",
         timezone="Europe/London",
         max_retries=3, next_run_at=now + timedelta(hours=2)),
    # THE DEMO TASK: fails forever -> shows the full retry pipeline live.
    Task(name="Flaky integration (demo failure path)",
         action_type="mock_command", action_target="always-fails",
         schedule_type="interval", schedule_value="60",
         max_retries=2, next_run_at=now + timedelta(seconds=20)),
]
db.add_all(tasks)
db.flush()

# A little believable history for the dashboard
hist = [
    (tasks[1], 1, "succeeded", "deleted 3 temp files"),
    (tasks[1], 1, "succeeded", "deleted 0 temp files"),
    (tasks[2], 1, "succeeded", "report generated (42 rows)"),
]
for task, attempt, status, output in hist:
    db.add(Execution(task_id=task.id, attempt=attempt, status=status,
                     scheduled_at=now - timedelta(hours=3),
                     started_at=now - timedelta(hours=3),
                     finished_at=now - timedelta(hours=3, seconds=-2),
                     output=output))
db.commit()

print(f"Seeded {len(tasks)} tasks at {now} UTC.")
for t in tasks:
    print(f"  - {t.name:<35} next run: {t.next_run_at} UTC")
db.close()
