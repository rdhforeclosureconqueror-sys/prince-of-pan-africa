import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function AdminDashboard() {
  const [profiles, setProfiles] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api("/admin/ai/profiles");
        setProfiles(res.profiles || []);
      } catch (err) {
        setError(err.message || "Failed to load profiles.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="admin-loading">Loading Profiles...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard">
      <h1>🧠 Simba Adaptive AI Evolution</h1>
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
          {profiles.map((p, i) => (
            <tr key={i}>
              <td>{p.member_id}</td>
              <td>{p.motion_avg}</td>
              <td>{p.voice_avg}</td>
              <td>{p.journal_avg}</td>
              <td>{p.consistency_score}</td>
              <td>{p.current_difficulty}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
