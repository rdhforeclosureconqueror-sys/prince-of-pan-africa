import React, { useEffect, useState, useRef } from "react";
import "./adminDashboard.css";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState([]);
  const wsRef = useRef(null);

  // 🧠 Load overview data
  async function fetchOverview() {
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

  // 🔁 Auto-refresh every 60 seconds
  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 60000);
    return () => clearInterval(interval);
  }, []);

  // 🕸️ Real-time feed via WebSocket
  useEffect(() => {
    const wsUrl =
      import.meta.env.VITE_WS_URL?.replace("http", "ws") ||
      "wss://api.simbawaujamaa.com";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("🟢 Admin WS connected");
      ws.send(
        JSON.stringify({
          type: "admin_register",
          member_id: "admin_" + Date.now(),
          role: "admin",
        })
      );
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log("📡 Admin WS message:", msg);

      // Inject new events into dashboard feed
      if (msg.type === "share_event" || msg.type === "review_submitted" || msg.type === "star_award_event") {
        setActivity((prev) => [
          {
            type: msg.type,
            member_id: msg.member_id,
            desc:
              msg.type === "share_event"
                ? `Shared on ${msg.share_platform}`
                : msg.type === "review_submitted"
                ? `Review video submitted: ${msg.business_name}`
                : `⭐ ${msg.delta} STAR awarded`,
            created_at: msg.created_at || new Date().toISOString(),
          },
          ...prev,
        ]);
      }
    };

    ws.onclose = () => console.log("🔴 Admin WS disconnected");
    return () => ws.close();
  }, []);

  if (loading) return <div className="admin-loading">Loading dashboard...</div>;
  if (!data) return <div className="admin-error">⚠️ Could not load dashboard</div>;

  return (
    <div className="admin-dashboard">
      <h1>🦁 Simba Admin Dashboard</h1>

      <div className="admin-stats">
        <div className="stat-card">
          <h2>{data.member_count}</h2>
          <p>Members</p>
        </div>
        <div className="stat-card">
          <h2>{data.total_shares}</h2>
          <p>Shares</p>
        </div>
        <div className="stat-card">
          <h2>{data.total_stars}</h2>
          <p>Stars Awarded</p>
        </div>
        <div className="stat-card">
          <h2>{data.total_bd}</h2>
          <p>Black Dollars</p>
        </div>
      </div>

      <section className="activity-feed">
        <h3>⚡ Live Activity Feed</h3>
        {activity.length === 0 ? (
          <p className="muted">No recent events yet...</p>
        ) : (
          activity.slice(0, 25).map((a, i) => (
            <div key={i} className="activity-item">
              <strong>{a.member_id}</strong> → <em>{a.desc}</em>
              <div className="activity-time">
                {new Date(a.created_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
