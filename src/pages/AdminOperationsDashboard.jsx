import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

const EMPTY_ARRAY = [];

export default function AdminOperationsDashboard() {
  const [overview, setOverview] = useState(null);
  const [members, setMembers] = useState(EMPTY_ARRAY);
  const [profiles, setProfiles] = useState(EMPTY_ARRAY);
  const [holistic, setHolistic] = useState(EMPTY_ARRAY);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [overviewRes, membersRes, profilesRes, holisticRes] = await Promise.all([
          api("/admin/ai/overview"),
          api("/admin/ai/members"),
          api("/admin/ai/profiles"),
          api("/admin/holistic/overview"),
        ]);

        if (!mounted) return;
        setOverview(overviewRes?.data || {});
        setMembers(membersRes?.members || EMPTY_ARRAY);
        setProfiles(profilesRes?.profiles || EMPTY_ARRAY);
        setHolistic(holisticRes?.holistic || EMPTY_ARRAY);
      } catch (err) {
        if (!mounted) return;
        setError(err.message || "Failed to load admin operations data.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const totals = useMemo(() => overview?.totals || {}, [overview]);

  if (loading) return <div className="admin-loading">Loading Operations Deck...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard cosmic-readable-shell">
      <h1>🛰️ Operations Deck — Unified Admin Dashboard</h1>
      <p className="admin-subtext">
        Connected to <code>/admin/ai/overview</code>, <code>/admin/ai/members</code>, <code>/admin/ai/profiles</code>, and <code>/admin/holistic/overview</code>.
      </p>

      <div className="dashboard-grid">
        <div className="stat-card"><h2>{totals?.motions ?? 0}</h2><p>Motion Samples</p></div>
        <div className="stat-card"><h2>{totals?.voices ?? 0}</h2><p>Voice Samples</p></div>
        <div className="stat-card"><h2>{totals?.journals ?? 0}</h2><p>Journal Entries</p></div>
        <div className="stat-card"><h2>{totals?.avg_score ?? 0}</h2><p>Avg AI Score</p></div>
      </div>

      <section className="cosmic-section">
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
            {(overview?.byType || EMPTY_ARRAY).length === 0 ? (
              <tr>
                <td colSpan={3}>No performance metrics available yet.</td>
              </tr>
            ) : (
              (overview?.byType || EMPTY_ARRAY).map((t, i) => (
                <tr key={i}>
                  <td>{t.metric_type}</td>
                  <td>{t.avg_score}</td>
                  <td>{t.samples}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="cosmic-section">
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
            {(overview?.models || EMPTY_ARRAY).length === 0 ? (
              <tr>
                <td colSpan={4}>No model versions published yet.</td>
              </tr>
            ) : (
              (overview?.models || EMPTY_ARRAY).map((m, i) => (
                <tr key={i}>
                  <td>{m.model_name}</td>
                  <td>{m.version}</td>
                  <td>{m.created_at ? new Date(m.created_at).toLocaleString() : "—"}</td>
                  <td>{JSON.stringify(m.parameters || {})}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="cosmic-section">
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
            {members.length === 0 ? (
              <tr>
                <td colSpan={7}>No member AI metrics yet. Data appears here after member activity and scoring routes write records.</td>
              </tr>
            ) : (
              members.map((m, i) => (
                <tr key={i}>
                  <td>{m.display_name}</td>
                  <td>{m.email}</td>
                  <td>{m.avg_score ?? "—"}</td>
                  <td>{m.total_metrics}</td>
                  <td>{m.motions}</td>
                  <td>{m.voices}</td>
                  <td>{m.journals}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="cosmic-section">
        <h2>🧠 Adaptive AI Profiles</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Motion Avg</th>
              <th>Voice Avg</th>
              <th>Journal Avg</th>
              <th>Consistency</th>
              <th>Difficulty</th>
            </tr>
          </thead>
          <tbody>
            {profiles.length === 0 ? (
              <tr>
                <td colSpan={6}>No adaptive profiles have been generated yet. Profiles are populated when adaptive scoring jobs publish results.</td>
              </tr>
            ) : (
              profiles.map((p, i) => (
                <tr key={i}>
                  <td>{p.member_id}</td>
                  <td>{p.motion_avg}</td>
                  <td>{p.voice_avg}</td>
                  <td>{p.journal_avg}</td>
                  <td>{p.consistency_score}</td>
                  <td>{p.current_difficulty}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="cosmic-section">
        <h2>🌍 Holistic Health Overview</h2>
        {holistic.length === 0 ? (
          <p>No holistic data available yet. This section depends on /admin/holistic/overview data feeds.</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Physical</th>
                <th>Mental</th>
                <th>Linguistic</th>
                <th>Cultural</th>
                <th>Overall</th>
              </tr>
            </thead>
            <tbody>
              {holistic.map((m, i) => (
                <tr key={i}>
                  <td>{m.member_id}</td>
                  <td>{m.physical_score?.toFixed(1) ?? "—"}</td>
                  <td>{m.mental_score?.toFixed(1) ?? "—"}</td>
                  <td>{m.linguistic_score?.toFixed(1) ?? "—"}</td>
                  <td>{m.cultural_score?.toFixed(1) ?? "—"}</td>
                  <td><b>{m.overall_health?.toFixed(1) ?? 0}%</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <footer className="admin-footer">
        🧠 Powered by SimbaBrain • <strong>Unified Operations Deck</strong>
      </footer>
    </div>
  );
}
