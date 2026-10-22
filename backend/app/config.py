"""Central configuration, read from environment variables.

STUDY NOTES
-----------
- Every tunable lives here so behaviour is discoverable and testable.
- Times: we use "naive UTC" datetimes everywhere (see utcnow()).
  Storing timezone-aware datetimes in SQLite is painful because SQLite
  has no real TIMESTAMP type; naive-UTC + one helper is the simplest
  correct approach for an MVP and maps 1:1 to Postgres TIMESTAMP.
"""
import os


def utcnow():
    """Current time as a naive UTC datetime.

    Naive means tzinfo=None. The RULE of this codebase is: every datetime
    stored in or compared against the database is naive UTC, produced by
    this function or derived from one. Never use datetime.now() (local time!).
    """
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scheduler.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Scheduler loop settings
SCHEDULER_TICK_SECONDS = int(os.getenv("SCHEDULER_TICK_SECONDS", "15"))
RETRY_BASE_DELAY_SECONDS = int(os.getenv("RETRY_BASE_DELAY_SECONDS", "30"))

# Minimum allowed interval between runs (seconds) - prevents users
# accidentally creating a task that fires every second and hammers the DB.
MIN_INTERVAL_SECONDS = 10
