import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "./adminDashboard.css";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadAdminData() {
      try {
        const res = await api("/admin/overview");
        setData(res.ok ? res : {
          ok: true,
          stats: { members_total: 1, shares_total: 0, stars_total: 0, bd_total: 0 },
          platformBreakdown: [],
          recentActivity: [],
        });
      } catch (err) {
        console.error("AdminDashboard load error:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadAdminData();
  }, []);

  if (loading) return <div className="admin-loading">Loading dashboard...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;
  if (!data) return <div className="admin-error">⚠️ No data found</div>;

  const { stats, platformBreakdown, recentActivity } = data;

  return (
    <div className="admin-dashboard">
      <h1>🦁 Simba Admin Dashboard</h1>

      <div className="admin-stats">
        <div className="stat-card"><h2>{stats.members_total}</h2><p>Members</p></div>
        <div className="stat-card"><h2>{stats.shares_total}</h2><p>Shares</p></div>
        <div className="stat-card"><h2>{stats.stars_total}</h2><p>Stars Awarded</p></div>
        <div className="stat-card"><h2>{stats.bd_total}</h2><p>Black Dollars Issued</p></div>
      </div>

      <section className="platform-section">
        <h3>Platform Breakdown</h3>
        <ul>
          {platformBreakdown?.length > 0 ? (
            platformBreakdown.map((p, i) => (
              <li key={i}>{p.platform || "Unknown"} — {p.count}</li>
            ))
          ) : (
            <li>No share data yet</li>
          )}
        </ul>
      </section>

      <section className="activity-feed">
        <h3>Recent Activity</h3>
        {recentActivity?.length > 0 ? (
          recentActivity.map((a, i) => (
            <div key={i} className="activity-item">
              <strong>{a.display_name}</strong> — <em>{a.category}</em>
              <div className="activity-time">{new Date(a.created_at).toLocaleString()}</div>
            </div>
          ))
        ) : (
          <div>No recent activity</div>
        )}
      </section>
    </div>
  );
}
