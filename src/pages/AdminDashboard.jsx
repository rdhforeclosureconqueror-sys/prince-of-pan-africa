// src/pages/AdminDashboard.jsx
import { useEffect, useState } from "react";
import { api } from "../api/api";
import UniverseOverlay from "../components/UniverseOverlay";
import "../styles/dashboard.css";

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [shares, setShares] = useState([]);
  const [members, setMembers] = useState([]);

  useEffect(() => {
    (async () => {
      const ov = await api("/admin/overview");
      const sh = await api("/admin/shares");
      const mb = await api("/admin/members");
      if (ov.ok) setOverview(ov);
      if (sh.ok) setShares(sh.shares);
      if (mb.ok) setMembers(mb.members);
    })();
  }, []);

  if (!overview)
    return <div className="admin-loading">Loading Simba Command Center...</div>;

  return (
    <>
      <UniverseOverlay />
      <div className="admin-dashboard">
        <h1>🦁 Simba Command Center</h1>

        <div className="dashboard-grid">
          <div className="stat-card">
            <h2>{overview.member_count}</h2>
            <p>Members</p>
          </div>
          <div className="stat-card">
            <h2>{overview.total_shares}</h2>
            <p>Shares</p>
          </div>
          <div className="stat-card">
            <h2>{overview.total_stars}</h2>
            <p>Participation Credits</p>
          </div>
          <div className="stat-card">
            <h2>{overview.total_bd}</h2>
            <p>Community Currency (Black Dollars)</p>
          </div>
        </div>

        <h2 style={{ marginTop: "3rem" }}>Recent Members</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {members.slice(0, 5).map((m, i) => (
              <tr key={i}>
                <td>{m.display_name || "—"}</td>
                <td>{m.email}</td>
                <td>{m.role}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2 style={{ marginTop: "3rem" }}>Recent Shares</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Platform</th>
              <th>URL</th>
            </tr>
          </thead>
          <tbody>
            {shares.slice(0, 5).map((s, i) => (
              <tr key={i}>
                <td>{s.member_id}</td>
                <td>{s.share_platform}</td>
                <td>
                  <a href={s.share_url} target="_blank" rel="noreferrer">
                    Link
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="admin-footer">
          Every Month Is Black History • Powered by <b>MufasaBrain</b>
        </div>
      </div>
    </>
  );
}
