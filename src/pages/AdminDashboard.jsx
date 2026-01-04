// ✅ src/pages/AdminDashboard.jsx
import { useEffect, useState } from "react";
import { api } from "../api/api";
import UniverseOverlay from "../components/UniverseOverlay";
import CosmicNav from "../components/CosmicNav";
import "../styles/dashboard.css";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await api("/admin/overview");
        if (res.ok) setData(res);
        else setErr("Failed to load overview");
      } catch (e) {
        setErr(e.message || "Network error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading)
    return (
      <div className="admin-loading">
        <UniverseOverlay />
        <CosmicNav />
        <div className="loading-text">
          Loading the 🦁 <b>Simba Command Center</b>...
        </div>
      </div>
    );

  if (err)
    return (
      <div className="admin-loading">
        <UniverseOverlay />
        <CosmicNav />
        <div className="loading-text">
          ⚠️ Error loading dashboard: {err}
        </div>
      </div>
    );

  const stats = data.stats || {};
  const platforms = data.platformBreakdown || [];
  const topMembers = data.topMembers || [];
  const activity = data.recentActivity || [];

  return (
    <>
      <UniverseOverlay />
      <CosmicNav />

      <div className="admin-dashboard">
        <header className="dashboard-header">
          <h1>
            <span role="img" aria-label="lion">
              🦁
            </span>{" "}
            Simba Command Center
          </h1>
          <p className="subtitle">
            Monitor engagement, stars, and community energy across the Simba
            universe.
          </p>
        </header>

        {/* 📊 Core Stats */}
        <div className="dashboard-grid cosmic-stats">
          <div className="stat-card cosmic-card">
            <h2>{stats.members_total ?? 0}</h2>
            <p>Members</p>
          </div>
          <div className="stat-card cosmic-card">
            <h2>{stats.shares_total ?? 0}</h2>
            <p>Shares</p>
          </div>
          <div className="stat-card cosmic-card">
            <h2>{stats.stars_total ?? 0}</h2>
            <p>Participation Credits ⭐</p>
          </div>
          <div className="stat-card cosmic-card">
            <h2>{stats.bd_total ?? 0}</h2>
            <p>Community Currency (BD)</p>
          </div>
        </div>

        {/* 🌍 Shares by Platform */}
        <section className="cosmic-section">
          <h2>Platform Breakdown</h2>
          <table className="admin-table cosmic-table">
            <thead>
              <tr>
                <th>Platform</th>
                <th>Shares</th>
              </tr>
            </thead>
            <tbody>
              {platforms.length > 0 ? (
                platforms.map((p, i) => (
                  <tr key={i}>
                    <td>{p.platform || "—"}</td>
                    <td>{p.count}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={2}>No share data yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        {/* 👥 Top Members */}
        <section className="cosmic-section">
          <h2>Top Members</h2>
          <table className="admin-table cosmic-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Shares</th>
              </tr>
            </thead>
            <tbody>
              {topMembers.length > 0 ? (
                topMembers.map((m, i) => (
                  <tr key={i}>
                    <td>{m.display_name}</td>
                    <td>{m.email}</td>
                    <td>{m.shares_count}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3}>No top members yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        {/* 🪶 Recent Activity */}
        <section className="cosmic-section">
          <h2>Recent Activity</h2>
          <ul className="activity-feed cosmic-activity">
            {activity.length > 0 ? (
              activity.map((a, i) => (
                <li key={i}>
                  <b>{a.display_name}</b> performed{" "}
                  <span className="highlight">{a.category}</span>{" "}
                  {a.context ? `(${a.context})` : ""} —{" "}
                  <span className="timestamp">
                    {new Date(a.created_at).toLocaleString()}
                  </span>
                </li>
              ))
            ) : (
              <li>No activity logged yet.</li>
            )}
          </ul>
        </section>

        <footer className="admin-footer cosmic-footer">
          <div>🌍 Every Month Is Black History</div>
          <div>
            Powered by <strong>MufasaBrain</strong>
          </div>
        </footer>
      </div>
    </>
  );
}
