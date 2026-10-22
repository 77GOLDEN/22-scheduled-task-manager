import { useCallback, useEffect, useState } from "react";
import TaskList from "./components/TaskList.jsx";
import TaskForm from "./components/TaskForm.jsx";
import ExecutionHistory from "./components/ExecutionHistory.jsx";
import { fetchTasks, createTask, updateTask, deleteTask, fetchExecutions } from "./api.js";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [apiError, setApiError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      setTasks(await fetchTasks());
      setApiError(null);
    } catch (err) {
      setApiError("Cannot reach the API: " + err.message);
    }
  }, []);

  // initial load + polling. 30s polling replaces WebSockets for the MVP:
  // simpler, and the countdown makes the UI feel live anyway.
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30000);
    return () => clearInterval(id);
  }, [refresh]);

  // load history whenever a different task is selected
  useEffect(() => {
    if (selectedId) fetchExecutions(selectedId).then(setExecutions);
    else setExecutions([]);
  }, [selectedId]);

  async function handleCreate(data) {
    await createTask(data);
    await refresh();
  }

  async function handleToggle(task) {
    const status = task.status === "active" ? "paused" : "active";
    await updateTask(task.id, { status });
    await refresh();
  }

  async function handleDelete(id) {
    await deleteTask(id);
    if (selectedId === id) setSelectedId(null);
    await refresh();
  }

  return (
    <main className="container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Scheduler / Operations</p>
          <h1>Scheduled Task Manager</h1>
          <p className="page-subtitle">Create schedules, track upcoming runs, and review every execution from one place.</p>
        </div>
        <div className="header-actions">
          <span className="live-indicator">Updates every 30 seconds</span>
          <button className="refresh-button" onClick={refresh}>Refresh</button>
        </div>
      </header>
      {apiError && <p className="error">{apiError}</p>}
      <TaskForm onCreate={handleCreate} />
      <TaskList tasks={tasks} selectedId={selectedId} onSelect={setSelectedId}
                onToggle={handleToggle} onDelete={handleDelete} />
      {selectedId && <ExecutionHistory executions={executions} />}
    </main>
  );
}
