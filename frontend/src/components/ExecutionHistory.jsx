const STATUS_CLASS = {
  succeeded: "succeeded", failed: "failed",
  exhausted: "failed", running: "running", queued: "queued",
};

export default function ExecutionHistory({ executions }) {
  return (
    <section className="history" aria-labelledby="history-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Selected task</p>
          <h2 id="history-heading">Execution history</h2>
          <p>Recent attempts, outcomes, and any error details.</p>
        </div>
        <span className="section-count">{executions.length} {executions.length === 1 ? "RUN" : "RUNS"}</span>
      </div>
      {executions.length === 0 && <p className="muted history-empty">No executions recorded yet.</p>}
      <div className="table-scroll">
      <table className="task-table">
        <thead>
          <tr><th>Attempt</th><th>Status</th><th>Scheduled</th><th>Result</th></tr>
        </thead>
        <tbody>
          {executions.map((ex) => (
            <tr key={ex.id}>
              <td>#{ex.attempt}</td>
              <td><span className={"badge " + STATUS_CLASS[ex.status]}>{ex.status}</span></td>
              <td>{new Date(ex.scheduled_at + "Z").toLocaleString()}</td>
              <td className="result">{ex.error_message || ex.output || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </section>
  );
}
