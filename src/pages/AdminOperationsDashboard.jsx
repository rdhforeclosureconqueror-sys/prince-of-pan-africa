import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

const EMPTY_ARRAY = [];

const OVERVIEW_ROUTE_CANDIDATES = ["/admin/ai/overview", "/admin/overview"];

const METRIC_CARDS = [
  ["total_users", "Total Users"],
  ["total_member_profiles", "Member Profiles"],
  ["total_activity_logs", "Activity Logs"],
  ["total_leadership_assessments", "Leadership Assessments"],
  ["total_audiobooks", "Audiobooks"],
  ["total_audiobook_progress_records", "Audiobook Progress Records"],
  ["total_reflections", "Reflections"],
  ["new_users_last_7_days", "New Users (Last 7 Days)"],
  ["active_users_last_7_days", "Active Users (Last 7 Days)"],
];

function formatError(err) {
  if (!err) return "Failed to load admin operations data.";
  if (err.status === 401) {
    return "You are not signed in. Please log in with an admin account to view the Operations Deck.";
  }
  if (err.status === 403) {
    return "Your account is signed in but does not have permission to view admin analytics.";
  }
  return err.message || "Failed to load admin operations data.";
}

export default function AdminOperationsDashboard() {
  const [overview, setOverview] = useState(null);
  const [activityItems, setActivityItems] = useState(EMPTY_ARRAY);
  const [overviewRouteUsed, setOverviewRouteUsed] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadOverview = async () => {
      let lastError;
      for (const route of OVERVIEW_ROUTE_CANDIDATES) {
        try {
          const res = await api(route);
          return { route, payload: res };
        } catch (err) {
          lastError = err;
          if (err?.status === 401 || err?.status === 403) {
            throw err;
          }
        }
      }
      throw lastError || new Error("Unable to load overview route.");
    };

    (async () => {
      try {
        const [overviewResult, activityRes] = await Promise.all([
          loadOverview(),
          api("/admin/activity-stream"),
        ]);

        if (!mounted) return;
        setOverviewRouteUsed(overviewResult.route);
        setOverview(overviewResult.payload?.data || {});
        setActivityItems(activityRes?.items || EMPTY_ARRAY);
      } catch (err) {
        if (!mounted) return;
        setError(formatError(err));
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const metrics = useMemo(() => overview?.metrics || {}, [overview]);
  const usersByRole = metrics?.users_by_role?.value || {};

  if (loading) return <div className="admin-loading">Loading Operations Deck...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard cosmic-readable-shell">
      <h1>🛰️ Operations Deck — Unified Admin Dashboard</h1>
      <p className="admin-subtext">
        Connected to <code>{overviewRouteUsed || "/admin/ai/overview"}</code> and <code>/admin/activity-stream</code>.
      </p>
      <p className="admin-subtext">
        Data source: <strong>{overview?.source || "unknown"}</strong>
      </p>

      <div className="dashboard-grid">
        {METRIC_CARDS.map(([key, label]) => (
          <div className="stat-card" key={key}>
            <h2>{metrics?.[key]?.value ?? "—"}</h2>
            <p>{label}</p>
          </div>
        ))}
      </div>

      <section className="cosmic-section">
        <h2>👥 Users by Role</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Role</th>
              <th>Users</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(usersByRole).length === 0 ? (
              <tr>
                <td colSpan={2}>No role distribution data available.</td>
              </tr>
            ) : (
              Object.entries(usersByRole).map(([role, count]) => (
                <tr key={role || "unknown"}>
                  <td>{role || "unknown"}</td>
                  <td>{count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="cosmic-section">
        <h2>📜 Activity Stream (Real ActivityLog Rows)</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User ID</th>
              <th>Action</th>
              <th>Timestamp</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {activityItems.length === 0 ? (
              <tr>
                <td colSpan={5}>No activity logs yet.</td>
              </tr>
            ) : (
              activityItems.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.user_id}</td>
                  <td>{item.action}</td>
                  <td>{item.timestamp ? new Date(item.timestamp).toLocaleString() : "—"}</td>
                  <td>{item.data_source || "unknown"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <footer className="admin-footer">
        🧠 Powered by SimbaBrain • <strong>Unified Operations Deck</strong>
      </footer>
    </div>
  );
}
