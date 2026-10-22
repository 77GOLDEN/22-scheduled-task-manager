// Thin API client. Every component talks to the backend THROUGH this file
// (never raw fetch in components) so mocks stay easy to swap in/out.

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

import { mockTasks, mockExecutions } from "./mockData.js";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    // FastAPI returns 422 errors as {detail: [{msg, loc}, ...]}
    const body = await res.json().catch(() => ({}));
    const msg = Array.isArray(body.detail)
      ? body.detail.map((d) => d.msg).join("; ")
      : body.detail || res.statusText;
    throw new Error(msg);
  }
  return res.json();
}

export function fetchTasks() {
  return USE_MOCK ? Promise.resolve(mockTasks) : request("/tasks");
}

export function createTask(data) {
  return USE_MOCK
    ? Promise.resolve({ ...data, id: crypto.randomUUID(), status: "active",
                        next_run_at: new Date().toISOString(), created_at: new Date().toISOString() })
    : request("/tasks", { method: "POST", body: JSON.stringify(data) });
}

export function updateTask(id, data) {
  return USE_MOCK ? Promise.resolve({ id, ...data }) : request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteTask(id) {
  return USE_MOCK ? Promise.resolve() : request(`/tasks/${id}`, { method: "DELETE" });
}

export function fetchExecutions(taskId) {
  if (USE_MOCK) return Promise.resolve(mockExecutions.filter((e) => e.task_id === taskId));
  return request(`/tasks/${taskId}/executions`);
}
