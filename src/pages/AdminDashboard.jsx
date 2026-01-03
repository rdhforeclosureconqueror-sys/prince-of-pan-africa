// ✅ src/pages/AdminDashboard.jsx
import { useEffect, useState } from "react";
import { api } from "../api/api";
import UniverseOverlay from "../components/UniverseOverlay";
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
        Loading the 🦁 <b>Simba Command Center</b>...
      </div>
    );

  if (err)
    return (
      <div className="admin-loading">
        ⚠️ Error loading dashboard: {err}
      </div>
    );

  const stats = data.stats || {};
  const platforms = data.platformBreakdown || [];
  const topMembers = data.topMembers || [];
  const activity = data.recentActivity || [];

  return (
    <>
      <UniverseOverlay />
      <div className="admin-dashboard">
        <h1>🦁 Simba Command Center</h1>

        {/* 📊 Core Stats */}
        <div className="dashboard-grid">
          <div className="stat-card">
            <h2>{stats.members_total ?? 0}</h2>
            <p>Members</p>
          </div>
          <div className="stat-card">
            <h2>{stats.shares_total ?? 0}</h2>
            <p>Shares</p>
          </div>
          <div className="stat-card">
            <h2>{stats.stars_total ?? 0}</h2>
            <p>Participation Credits (⭐)</p>
          </div>
          <div className="stat-card">
            <h2>{stats.bd_total ?? 0}</h2>
            <p>Community Currency (BD)</p>
          </div>
        </div>

        {/* 🌍 Shares by Platform */}
        <section style={{ marginTop: "3rem" }}>
          <h2>Platform Breakdown</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Platform</th>
                <th>Shares</th>
              </tr>
            </thead>
            <tbody>
              {platforms.map((p, i) => (
                <tr key={i}>
                  <td>{p.platform || "—"}</td>
                  <td>{p.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* 👥 Top Members */}
        <section style={{ marginTop: "3rem" }}>
          <h2>Top Members</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Shares</th>
              </tr>
            </thead>
            <tbody>
              {topMembers.map((m, i) => (
                <tr key={i}>
                  <td>{m.display_name}</td>
                  <td>{m.email}</td>
                  <td>{m.shares_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* 🪶 Recent Activity */}
        <section style={{ marginTop: "3rem" }}>
          <h2>Recent Activity</h2>
          <ul className="activity-feed">
            {activity.map((a, i) => (
              <li key={i}>
                <b>{a.display_name}</b> did a <i>{a.category}</i>{" "}
                {a.context ? `(${a.context})` : ""} at{" "}
                {new Date(a.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </section>

        <footer className="admin-footer">
          Every Month Is Black History · <strong>Powered by MufasaBrain</strong>
        </footer>
      </div>
    </>
  );
}
