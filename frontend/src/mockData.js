// Mock data used when VITE_USE_MOCK=true (Days 2-3 of the plan:
// build the UI before the backend exists).
// Timestamps are naive UTC strings, exactly like the API returns.
const soon = (s) => new Date(Date.now() + s * 1000).toISOString().slice(0, 19);

export const mockTasks = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    name: "Cleanup temp files",
    action_type: "mock_command",
    action_target: "cleanup-temp-files",
    schedule_type: "interval",
    schedule_value: "3600",
    timezone: "UTC",
    max_retries: 3,
    status: "active",
    next_run_at: soon(600),
    created_at: soon(-3600),
  },
  {
    id: "22222222-2222-2222-2222-222222222222",
    name: "Flaky integration",
    action_type: "mock_command",
    action_target: "always-fails",
    schedule_type: "interval",
    schedule_value: "60",
    timezone: "UTC",
    max_retries: 2,
    status: "active",
    next_run_at: soon(20),
    created_at: soon(-7200),
  },
];

export const mockExecutions = [
  {
    id: "a1", task_id: mockTasks[0].id, attempt: 1, status: "succeeded",
    scheduled_at: soon(-3600), started_at: soon(-3600), finished_at: soon(-3599),
    error_message: null, output: "deleted 3 temp files",
  },
  {
    id: "a2", task_id: mockTasks[1].id, attempt: 1, status: "failed",
    scheduled_at: soon(-120), started_at: soon(-120), finished_at: soon(-119),
    error_message: "simulated permanent failure (mock command)", output: null,
  },
  {
    id: "a3", task_id: mockTasks[1].id, attempt: 2, status: "queued",
    scheduled_at: soon(30), started_at: null, finished_at: null,
    error_message: null, output: null,
  },
];
