# API contract (agreed on Day 1 - frontend and backend build against this)

Base URL: `http://localhost:8000` (dev). All timestamps are naive UTC
strings, e.g. `"2026-10-20T09:00:00"`.

Errors: 404 `{"detail": "task not found"}`; 422
`{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.

## POST /tasks - create (201)
```json
{
  "name": "Cleanup temp files",
  "action_type": "mock_command",
  "action_target": "cleanup-temp-files",
  "schedule_type": "interval",
  "schedule_value": "3600",
  "timezone": "UTC",
  "max_retries": 3
}
```
Response echoes the task plus generated fields:
```json
{
  "id": "3fa8...",
  "name": "Cleanup temp files",
  "action_type": "mock_command",
  "action_target": "cleanup-temp-files",
  "schedule_type": "interval",
  "schedule_value": "3600",
  "timezone": "UTC",
  "max_retries": 3,
  "status": "active",
  "next_run_at": "2026-10-20T10:00:00",
  "created_at": "2026-10-20T09:00:00"
}
```

Validation rules (all return 422 when broken):
- `name`: 1-120 chars
- `action_type`: `"http"` | `"mock_command"`
- `action_target`: http -> must start with `http(s)://`;
  mock_command -> must be one of `cleanup-temp-files`, `generate-report`, `always-fails`
- `schedule_type`: `"interval"` | `"cron"`
- `schedule_value`: interval -> integer seconds >= 10; cron -> valid 5-field expression
- `max_retries`: 0-10 (default 3). Retries AFTER the first attempt.

## GET /tasks - list
Returns an array of task objects as above.

## GET /tasks/{id}
Single task object, or 404.

## PATCH /tasks/{id}
Any subset of: `name`, `schedule_type`, `schedule_value`, `timezone`,
`max_retries`, `status` (`"active"` | `"paused"`). Changing the schedule
or resuming recomputes `next_run_at` from now.
```json
{"status": "paused"}
```

## DELETE /tasks/{id} - (204, no body)
Also deletes all of the task's executions (cascade).

## GET /tasks/{id}/executions
Up to 50 most recent executions, newest first:
```json
[{
  "id": "9c1e...",
  "task_id": "3fa8...",
  "attempt": 2,
  "status": "failed",
  "scheduled_at": "2026-10-20T09:00:30",
  "started_at": "2026-10-20T09:00:30",
  "finished_at": "2026-10-20T09:00:31",
  "error_message": "simulated permanent failure (mock command)",
  "output": null
}]
```
Status values: `queued`, `running`, `succeeded`, `failed`, `exhausted`.

## GET /tasks/{id}/next-runs?count=5
Predicted upcoming run times (read-only demo helper).

## GET /executions?task_id=&limit=
Global history view, newest first.
