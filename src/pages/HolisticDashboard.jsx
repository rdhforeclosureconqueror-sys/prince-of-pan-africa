import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function HolisticDashboard() {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api("/admin/holistic/overview");
        setData(res.holistic || []);
      } catch (err) {
        setError(err.message || "Unable to connect to Simba API");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="admin-loading">Loading Holistic Overview...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard">
      <h1>🌍 Simba Holistic Health Brain</h1>
      {data.length === 0 ? (
        <p>No holistic data available yet.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Physical</th>
              <th>Mental</th>
              <th>Linguistic</th>
              <th>Cultural</th>
              <th>Overall</th>
            </tr>
          </thead>
          <tbody>
            {data.map((m, i) => (
              <tr key={i}>
                <td>{m.member_id}</td>
                <td>{m.physical_score?.toFixed(1) ?? "—"}</td>
                <td>{m.mental_score?.toFixed(1) ?? "—"}</td>
                <td>{m.linguistic_score?.toFixed(1) ?? "—"}</td>
                <td>{m.cultural_score?.toFixed(1) ?? "—"}</td>
                <td><b>{m.overall_health?.toFixed(1) ?? 0}%</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
