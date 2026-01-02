import { useEffect, useState } from "react";
import { api } from "../../api/api";
import "./admin.css";

export default function AdminPage() {
  const [overview, setOverview] = useState(null);
  const [members, setMembers] = useState([]);
  const [shares, setShares] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    (async () => {
      const ov = await api("/admin/overview");
      const mb = await api("/admin/members");
      const sh = await api("/admin/shares");
      const rv = await api("/admin/reviews");
      const ac = await api("/admin/activity-stream");
      if (ov.ok) setOverview(ov);
      if (mb.ok) setMembers(mb.members);
      if (sh.ok) setShares(sh.shares);
      if (rv.ok) setReviews(rv.reviews);
      if (ac.ok) setActivity(ac.items);
    })();
  }, []);

  if (!overview) return <div className="admin-loading">Loading Dashboard...</div>;

  return (
    <div className="admin-shell">
      <h1>🦁 Simba Command Center</h1>
      <section className="admin-overview">
        <div className="stat"><h2>{overview.member_count}</h2><p>Members</p></div>
        <div className="stat"><h2>{overview.total_shares}</h2><p>Shares</p></div>
        <div className="stat"><h2>{overview.total_stars}</h2><p>Total STARs</p></div>
        <div className="stat"><h2>{overview.total_bd}</h2><p>Total BD</p></div>
      </section>

      <section>
        <h2>Recent Shares</h2>
        <table className="admin-table">
          <thead><tr><th>Member</th><th>Platform</th><th>URL</th><th>Date</th></tr></thead>
          <tbody>
            {shares.map((s, i) => (
              <tr key={i}><td>{s.member_id}</td><td>{s.share_platform}</td><td>{s.share_url}</td><td>{new Date(s.created_at).toLocaleString()}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Pending Reviews</h2>
        <table className="admin-table">
          <thead><tr><th>Business</th><th>Member</th><th>Status</th><th>Video</th></tr></thead>
          <tbody>
            {reviews.map((r, i) => (
              <tr key={i}><td>{r.business_name}</td><td>{r.member_id}</td><td>{r.status}</td><td><a href={r.video_url} target="_blank">Watch</a></td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>System Activity</h2>
        <ul className="activity-feed">
          {activity.map((a, i) => (
            <li key={i}>{a.type}: {a.reason} ({a.delta}) — {new Date(a.created_at).toLocaleString()}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
