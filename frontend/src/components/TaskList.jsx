import Countdown from "./Countdown.jsx";

export default function TaskList({ tasks, selectedId, onSelect, onToggle, onDelete }) {
  return (
    <section className="task-section" aria-labelledby="tasks-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Your automations</p>
          <h2 id="tasks-heading">Scheduled tasks</h2>
          <p>Monitor status and the next scheduled run.</p>
        </div>
        <span className="section-count">{tasks.length} {tasks.length === 1 ? "TASK" : "TASKS"}</span>
      </div>
      <div className="table-scroll">
      <table className="task-table">
      <thead>
        <tr>
          <th>Name</th><th>Schedule</th><th>Status</th>
          <th>Next run</th><th></th>
        </tr>
      </thead>
      <tbody>
        {tasks.map((t) => (
          <tr key={t.id} className={t.id === selectedId ? "selected" : ""}
              aria-selected={t.id === selectedId}
              onClick={() => onSelect(t.id)}>
            <td>
              <strong>{t.name}</strong>
              <div className="muted">{t.action_type}: {t.action_target}</div>
            </td>
            <td>
              {t.schedule_type === "interval"
                ? `every ${Number(t.schedule_value).toLocaleString()}s`
                : `cron "${t.schedule_value}"`}
              {t.timezone !== "UTC" && <div className="muted">{t.timezone}</div>}
            </td>
            <td><span className={"badge " + t.status}>{t.status}</span></td>
            <td>{t.status === "active" && t.next_run_at
                  ? <Countdown iso={t.next_run_at} />
                  : "—"}</td>
            <td onClick={(e) => e.stopPropagation()}>
              <button onClick={() => onToggle(t)}>{t.status === "active" ? "Pause" : "Resume"}</button>
              <button className="danger" onClick={() => onDelete(t.id)}>Delete</button>
            </td>
          </tr>
        ))}
        {tasks.length === 0 && (
          <tr className="empty-row"><td colSpan="5">No tasks yet — create one above to get started.</td></tr>
        )}
      </tbody>
    </table>
      </div>
    </section>
  );
}
