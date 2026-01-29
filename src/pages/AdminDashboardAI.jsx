import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function AdminDashboardAI() {
  const [overview, setOverview] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const o = await api("/admin/ai/overview");
        const m = await api("/admin/ai/members");
        setOverview(o.data || {});
        setMembers(m.members || []);
      } catch (err) {
        setError(err.message || "Failed to load AI metrics.");
      }
    })();
  }, []);

  if (error) return <div className="admin-error">⚠️ {error}</div>;
  if (!overview) return <div className="admin-loading">Loading AI Overview...</div>;

  return (
    <>
      <div className="admin-dashboard">
        <h1>🧠 Simba AI Metrics Command Center</h1>

        <div className="dashboard-grid">
          <div className="stat-card"><h2>{overview?.totals?.motions ?? 0}</h2><p>Motion Samples</p></div>
          <div className="stat-card"><h2>{overview?.totals?.voices ?? 0}</h2><p>Voice Samples</p></div>
          <div className="stat-card"><h2>{overview?.totals?.journals ?? 0}</h2><p>Journal Entries</p></div>
          <div className="stat-card"><h2>{overview?.totals?.avg_score ?? 0}</h2><p>Avg AI Score</p></div>
        </div>

        <section>
          <h2>📈 Performance by Type</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Avg Score</th>
                <th>Samples</th>
              </tr>
            </thead>
            <tbody>
              {overview?.byType?.map((t, i) => (
                <tr key={i}>
                  <td>{t.metric_type}</td>
                  <td>{t.avg_score}</td>
                  <td>{t.samples}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <h2>🤖 Model Versions</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Version</th>
                <th>Created</th>
                <th>Parameters</th>
              </tr>
            </thead>
            <tbody>
              {overview?.models?.map((m, i) => (
                <tr key={i}>
                  <td>{m.model_name}</td>
                  <td>{m.version}</td>
                  <td>{new Date(m.created_at).toLocaleString()}</td>
                  <td>{JSON.stringify(m.parameters || {})}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <h2>👥 Member AI Scores</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Avg Score</th>
                <th>Total Metrics</th>
                <th>Motion</th>
                <th>Voice</th>
                <th>Journal</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m, i) => (
                <tr key={i}>
                  <td>{m.display_name}</td>
                  <td>{m.email}</td>
                  <td>{m.avg_score ?? "—"}</td>
                  <td>{m.total_metrics}</td>
                  <td>{m.motions}</td>
                  <td>{m.voices}</td>
                  <td>{m.journals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <footer className="admin-footer">
          🧠 Powered by SimbaBrain • <strong>AI Evolution Engine</strong>
        </footer>
      </div>
    </>
  );
}
