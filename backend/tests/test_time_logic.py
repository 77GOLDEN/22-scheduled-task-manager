"""Pure-function tests: the scheduling math that everything else depends on.

These have no database and no HTTP - the fastest, most valuable kind of test.
"""
from datetime import datetime, timedelta

from app.scheduler import compute_next_run, backoff_delay
from app.config import RETRY_BASE_DELAY_SECONDS


class FakeTask:
    """Minimal stand-in for the ORM object - pure functions shouldn't need a DB."""
    def __init__(self, schedule_type, schedule_value):
        self.schedule_type = schedule_type
        self.schedule_value = schedule_value


def test_interval_next_run_adds_seconds():
    task = FakeTask("interval", "3600")
    start = datetime(2026, 10, 20, 9, 0, 0)
    assert compute_next_run(task, start) == datetime(2026, 10, 20, 10, 0, 0)


def test_cron_next_run_finds_next_matching_instant():
    task = FakeTask("cron", "0 9 * * *")  # every day at 09:00
    start = datetime(2026, 10, 20, 15, 30, 0)
    assert compute_next_run(task, start) == datetime(2026, 10, 21, 9, 0, 0)


def test_cron_next_run_same_day_if_before():
    task = FakeTask("cron", "0 9 * * *")
    start = datetime(2026, 10, 20, 8, 0, 0)
    assert compute_next_run(task, start) == datetime(2026, 10, 20, 9, 0, 0)


def test_backoff_doubles_each_attempt():
    base = RETRY_BASE_DELAY_SECONDS
    assert backoff_delay(1) == timedelta(seconds=base * 1)
    assert backoff_delay(2) == timedelta(seconds=base * 2)
    assert backoff_delay(3) == timedelta(seconds=base * 4)
