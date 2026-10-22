import { useState } from "react";

const EMPTY = {
  name: "", action_type: "mock_command",
  action_target: "cleanup-temp-files",
  schedule_type: "interval", schedule_value: "300",
  timezone: "UTC", max_retries: 3,
};

export default function TaskForm({ onCreate }) {
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await onCreate({ ...form, max_retries: Number(form.max_retries) });
      setForm(EMPTY);
    } catch (err) {
      setError(err.message); // server-side validation shown to the user
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="task-form" onSubmit={submit}>
      <div className="form-heading">
        <div>
          <p className="section-kicker">Configure a schedule</p>
          <h2>New task</h2>
          <p>Choose an action and decide when it should run.</p>
        </div>
        <span className="section-count">AUTOMATION</span>
      </div>
      <div className="row">
        <input placeholder="Task name" value={form.name} onChange={set("name")} required />
        <select value={form.action_type} onChange={set("action_type")}>
          <option value="mock_command">Mock command</option>
          <option value="http">HTTP GET</option>
        </select>
        {form.action_type === "http" ? (
          <input placeholder="https://example.com/api" value={form.action_target} onChange={set("action_target")} required />
        ) : (
          <select value={form.action_target} onChange={set("action_target")}>
            <option value="cleanup-temp-files">cleanup-temp-files</option>
            <option value="generate-report">generate-report</option>
            <option value="always-fails">always-fails (demo failure)</option>
          </select>
        )}
      </div>
      <div className="row">
        <select value={form.schedule_type} onChange={set("schedule_type")}>
          <option value="interval">Every N seconds</option>
          <option value="cron">Cron expression</option>
        </select>
        <input placeholder={form.schedule_type === "interval" ? "300" : "0 9 * * *"}
               value={form.schedule_value} onChange={set("schedule_value")} required />
        <input placeholder="Timezone (UTC)" value={form.timezone} onChange={set("timezone")} />
        <input type="number" min="0" max="10" value={form.max_retries}
               onChange={set("max_retries")} title="Max retries" />
        <button type="submit" disabled={busy}>{busy ? "Creating…" : "Create task"}</button>
      </div>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
