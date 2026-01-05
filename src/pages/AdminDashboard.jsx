import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function AIDashboard() {
  const [profiles, setProfiles] = useState([]);

  useEffect(() => {
    (async () => {
      const data = await api("/admin/ai/profiles");
      if (data.ok) setProfiles(data.profiles);
    })();
  }, []);

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
