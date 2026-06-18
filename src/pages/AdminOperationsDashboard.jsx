import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

const EMPTY_ARRAY = [];

const OVERVIEW_ROUTE_CANDIDATES = ["/admin/ai/overview", "/admin/overview"];


const DISCORD_ACTIONS = [
  { label: "Test Discord Health", method: "GET", path: "/discord/health" },
  { label: "Post Daily Black Economics Fact", method: "POST", path: "/discord/black-economics/daily", body: {} },
  { label: "Dry Run Black Economics Fact", method: "POST", path: "/discord/black-economics/dry-run", body: {} },
  { label: "Post Regional Prompt — North", method: "POST", path: "/discord/regional/north", body: {} },
  { label: "Post Regional Prompt — South", method: "POST", path: "/discord/regional/south", body: {} },
  { label: "Post Regional Prompt — East", method: "POST", path: "/discord/regional/east", body: {} },
  { label: "Post Regional Prompt — West", method: "POST", path: "/discord/regional/west", body: {} },
  { label: "Send Test Verification Request", method: "POST", path: "/discord/test/verification-request", body: {} },
  { label: "Send Test Celebration", method: "POST", path: "/discord/test/celebration", body: {} },
  { label: "Send Test Bot Log Message", method: "POST", path: "/discord/test/bot-log", body: {} },
];

function sanitizeDiscordResult(result) {
  return {
    success: Boolean(result?.success ?? result?.ok),
    target_channel: result?.target_channel || "—",
    message_preview: result?.message_preview || result?.content || "—",
    error: result?.error || result?.detail || null,
    timestamp: result?.timestamp || new Date().toISOString(),
    raw: result,
  };
}

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
  const [discordResults, setDiscordResults] = useState({});
  const [discordRunning, setDiscordRunning] = useState(null);

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

  const runDiscordAction = async (action) => {
    setDiscordRunning(action.path);
    try {
      const result = await api(action.path, {
        method: action.method,
        ...(action.method === "POST" ? { body: JSON.stringify(action.body || {}) } : {}),
      });
      setDiscordResults((current) => ({ ...current, [action.path]: sanitizeDiscordResult(result) }));
    } catch (err) {
      setDiscordResults((current) => ({
        ...current,
        [action.path]: sanitizeDiscordResult({
          ok: false,
          target_channel: "—",
          message_preview: "—",
          error: err?.message || "Discord action failed.",
          timestamp: new Date().toISOString(),
        }),
      }));
    } finally {
      setDiscordRunning(null);
    }
  };

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
        <h2>🦁 Discord Tools</h2>
        <p className="admin-subtext">Admin-authenticated controls for testing Simba Bot posts and regional automation. Secrets are never displayed.</p>
        <div className="dashboard-grid">
          {DISCORD_ACTIONS.map((action) => {
            const result = discordResults[action.path];
            return (
              <div className="stat-card" key={action.path}>
                <h3>{action.label}</h3>
                <button className="hero-btn hero-btn--secondary" type="button" onClick={() => runDiscordAction(action)} disabled={discordRunning === action.path}>
                  {discordRunning === action.path ? "Running..." : "Run"}
                </button>
                {result && (
                  <div className="admin-subtext">
                    <p><strong>Status:</strong> {result.success ? "✅ Success" : "❌ Failed"}</p>
                    <p><strong>Target channel:</strong> {result.target_channel}</p>
                    <p><strong>Message preview:</strong> {result.message_preview}</p>
                    {result.error && <p><strong>Error:</strong> {result.error}</p>}
                    <p><strong>Timestamp:</strong> {new Date(result.timestamp).toLocaleString()}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

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
