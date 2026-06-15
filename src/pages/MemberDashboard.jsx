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
          api("/member/overview", { method: "GET" }),
          api("/member/activity", { method: "GET" }),
        ]);

        if (!mounted) return;
        setOverview(overviewRes || null);
        setActivity(activityRes?.activity || activityRes?.items || []);
      } catch (err) {
        if (!mounted) return;
        if (err.status === 401) {
          setError("Authentication required. Please log in again to load your member dashboard.");
        } else if (err.status === 403) {
          setError("Your account is signed in but does not have member dashboard access. Please contact support.");
        } else {
          setError(err.message || "Unable to load your experience data yet.");
        }
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

  const summary = overview?.summary_stats || overview || {};
  const membership = overview?.membership || {};
  const builder = membership?.builder || {};
  const communityUpdates = Array.isArray(membership?.community_updates) ? membership.community_updates : [];
  const testingOpportunities = Array.isArray(builder?.testing_opportunities) ? builder.testing_opportunities : [];
  const contributionHistory = Array.isArray(builder?.contribution_history) ? builder.contribution_history : [];
  const isBuilder = Boolean(builder?.is_builder || membership?.type === "builder_member");

  return (
    <div className="admin-dashboard cosmic-readable-shell">
      <h1>🌟 Membership Dashboard</h1>

      <section className="membership-status-grid" aria-label="Membership status">
        <article className="membership-status-card">
          <span>Membership Status</span>
          <strong>{membership?.status || "active"}</strong>
        </article>
        <article className="membership-status-card">
          <span>Membership Type</span>
          <strong>{membership?.label || "Community Member"}</strong>
        </article>
        <article className="membership-status-card">
          <span>Orientation Status</span>
          <strong>{membership?.orientation_status || "not_started"}</strong>
        </article>
        <article className="membership-status-card">
          <span>Discord Status</span>
          <strong>{membership?.discord_status || "not_connected"}</strong>
        </article>
      </section>

      <div className="dashboard-grid">
        <div className="stat-card">
          <h2>{summary?.reading_minutes ?? 0}</h2>
          <p>Reading Minutes</p>
        </div>
        <div className="stat-card">
          <h2>{summary?.workouts_completed ?? 0}</h2>
          <p>Workouts Completed</p>
        </div>
        <div className="stat-card">
          <h2>{summary?.shares ?? 0}</h2>
          <p>Shared Posts</p>
        </div>
        <div className="stat-card">
          <h2>{summary?.streak_days ?? 0}</h2>
          <p>Consistency Streak</p>
        </div>
      </div>

      <section className="cosmic-section">
        <h2>📣 Community Updates</h2>
        {communityUpdates.length === 0 ? (
          <p>No community updates are posted yet.</p>
        ) : (
          <ul className="activity-feed">
            {communityUpdates.map((update) => (
              <li key={update}>{update}</li>
            ))}
          </ul>
        )}
      </section>

      {isBuilder ? (
        <section className="cosmic-section builder-dashboard-section">
          <h2>🛠️ Builder Participation</h2>
          <div className="builder-dashboard-grid">
            <article>
              <h3>Testing Opportunities</h3>
              {testingOpportunities.length === 0 ? (
                <p>No testing opportunities are posted yet.</p>
              ) : (
                <ul>
                  {testingOpportunities.map((opportunity) => (
                    <li key={opportunity}>{opportunity}</li>
                  ))}
                </ul>
              )}
            </article>
            <article>
              <h3>Contribution History</h3>
              {contributionHistory.length === 0 ? (
                <p>No Builder contributions have been tracked yet.</p>
              ) : (
                <ul>
                  {contributionHistory.map((contribution) => (
                    <li key={contribution.id || contribution.title}>{contribution.title || contribution.summary}</li>
                  ))}
                </ul>
              )}
            </article>
            <article>
              <h3>Feedback Participation</h3>
              <p>{builder?.feedback_participation?.summary || "Builder feedback tracking is being prepared."}</p>
            </article>
          </div>
        </section>
      ) : null}

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
