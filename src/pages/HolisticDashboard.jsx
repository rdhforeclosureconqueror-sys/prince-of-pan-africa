import { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/dashboard.css";

export default function HolisticDashboard() {
  const [data, setData] = useState([]);

  useEffect(() => {
    (async () => {
      const res = await api("/admin/holistic/overview");
      if (res.ok) setData(res.holistic);
    })();
  }, []);

  return (
    <div className="admin-dashboard">
      <h1>🌍 Simba Holistic Health Brain</h1>
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
              <td>{m.physical_score.toFixed(1)}</td>
              <td>{m.mental_score.toFixed(1)}</td>
              <td>{m.linguistic_score.toFixed(1)}</td>
              <td>{m.cultural_score.toFixed(1)}</td>
              <td><b>{m.overall_health.toFixed(1)}%</b></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
