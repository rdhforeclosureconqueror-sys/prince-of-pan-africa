import React, { useEffect, useState } from "react";
import "./adminDashboard.css";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch("/admin/overview", { credentials: "include" });
        const json = await res.json();
        if (json.ok) setData(json);
      } catch (err) {
        console.error("Failed to load admin data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="admin-loading">Loading dashboard...</div>;
  if (!data) return <div className="admin-error">⚠️ Could not load dashboard</div>;

  return (
    <div className="admin-dashboard">
      <h1>🦁 Simba Admin Dashboard</h1>

      <div className="admin-stats">
        <div className="stat-card">
          <h2>{data.stats.members_total}</h2>
          <p>Members</p>
        </div>
        <div className="stat-card">
          <h2>{data.stats.shares_total}</h2>
          <p>Shares</p>
        </div>
        <div className="stat-card">
          <h2>{data.stats.stars_total}</h2>
          <p>Stars Awarded</p>
        </div>
      </div>

      <section className="platform-section">
        <h3>Platform Breakdown</h3>
        <ul>
          {data.platformBreakdown.map((p) => (
            <li key={p.platform}>
              {p.platform || "Unknown"} — {p.count}
            </li>
          ))}
        </ul>
      </section>

      <section className="activity-feed">
        <h3>Recent Activity</h3>
        {data.recentActivity.map((a, i) => (
          <div key={i} className="activity-item">
            <strong>{a.display_name}</strong> did <em>{a.category}</em>  
            <div className="activity-time">
              {new Date(a.created_at).toLocaleString()}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
