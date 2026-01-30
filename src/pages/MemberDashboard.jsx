import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function MemberDashboard() {
  const [overview, setOverview] = useState(null);
  const [activity, setActivity] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [overviewRes, activityRes] = await Promise.all([
          api("/member/overview"),
          api("/member/activity"),
        ]);

        if (!mounted) return;
        setOverview(overviewRes || null);
        setActivity(activityRes?.activity || []);
      } catch (err) {
        if (!mounted) return;
        setError(err.message || "Unable to load your experience data yet.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div className="admin-loading">Loading your dashboard...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard">
      <h1>🌟 Member Experience Dashboard</h1>

      <div className="dashboard-grid">
        <div className="stat-card">
          <h2>{overview?.reading_minutes ?? 0}</h2>
          <p>Reading Minutes</p>
        </div>
        <div className="stat-card">
          <h2>{overview?.workouts_completed ?? 0}</h2>
          <p>Workouts Completed</p>
        </div>
        <div className="stat-card">
          <h2>{overview?.shares ?? 0}</h2>
          <p>Shared Posts</p>
        </div>
        <div className="stat-card">
          <h2>{overview?.streak_days ?? 0}</h2>
          <p>Consistency Streak</p>
        </div>
      </div>

      <section className="cosmic-section">
        <h2>📌 Recent Activity</h2>
        {activity.length === 0 ? (
          <p>No tracked activity yet. Start a lesson, share a post, or log a workout.</p>
        ) : (
          <ul className="activity-feed">
            {activity.map((item, idx) => (
              <li key={idx}>
                <span className="highlight">{item.title || item.type}</span>{" "}
                <span className="timestamp">{item.timestamp}</span>
                <div>{item.detail || item.description}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="cosmic-section">
        <h2>🧭 Experience Tracking</h2>
        <p>
          Your reading, workouts, and social shares are logged automatically. If you
          connect your sharing accounts or log sessions, they’ll appear here and sync
          to the operations deck.
        </p>
      </section>
    </div>
  );
}
