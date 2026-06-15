import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { BLACK_HISTORY_MONTHLY } from "../data/blackHistoryFacts";
import { TIMELINE_A_AFRICA_ORIGINS } from "../data/timelineA_africaOrigins";
import swahiliLessons from "../../public/languages/swahili_30days.json";
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

  const today = useMemo(() => new Date(), []);
  const dayOfYear = useMemo(() => {
    const startOfYear = new Date(today.getFullYear(), 0, 0);
    return Math.floor((today - startOfYear) / 86400000);
  }, [today]);
  const summary = overview?.summary_stats || overview || {};
  const membership = overview?.membership || {};
  const builder = membership?.builder || {};
  const communityUpdates = Array.isArray(membership?.community_updates) ? membership.community_updates : [];
  const testingOpportunities = Array.isArray(builder?.testing_opportunities) ? builder.testing_opportunities : [];
  const contributionHistory = Array.isArray(builder?.contribution_history) ? builder.contribution_history : [];
  const isBuilder = Boolean(builder?.is_builder || membership?.type === "builder_member");
  const memberName = overview?.profile?.name || overview?.user?.name || overview?.email || "Member";
  const swahiliDays = Array.isArray(swahiliLessons?.days) ? swahiliLessons.days : [];
  const swahiliLesson = swahiliDays.length ? swahiliDays[(dayOfYear - 1) % swahiliDays.length] : null;
  const swahiliWord = swahiliLesson?.words?.[0] || null;
  const monthName = today.toLocaleString("en-US", { month: "long" });
  const monthlyFacts = BLACK_HISTORY_MONTHLY[monthName] || [];
  const historicalFact = monthlyFacts.length
    ? monthlyFacts[(today.getDate() - 1) % monthlyFacts.length]
    : TIMELINE_A_AFRICA_ORIGINS[dayOfYear % TIMELINE_A_AFRICA_ORIGINS.length]?.summary;
  const featuredTimeline = TIMELINE_A_AFRICA_ORIGINS[dayOfYear % TIMELINE_A_AFRICA_ORIGINS.length];
  const recentActivity = activity.slice(0, 3);

  if (loading) return <div className="admin-loading">Loading your dashboard...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard member-launchpad cosmic-readable-shell">
      <header className="member-hero dashboard-header">
        <p className="member-kicker">Daily Community Hub</p>
        <h1>Welcome Back, {memberName}</h1>
        <p className="subtitle">Pick up one lesson, one community signal, and one concrete action for today.</p>
        <div className="member-quick-actions">
          <Link to="/library" className="member-action-btn">Open Library</Link>
          <Link to="/leadership" className="member-action-btn member-action-btn--secondary">Leadership Assessment</Link>
          <a href="/languages/swahili.html" className="member-action-btn member-action-btn--ghost">Swahili Lesson</a>
        </div>
      </header>

      <section className="membership-status-grid" aria-label="Membership status">
        <article className="membership-status-card"><span>Membership Status</span><strong>{membership?.status || "active"}</strong></article>
        <article className="membership-status-card"><span>Membership Type</span><strong>{membership?.label || "Community Member"}</strong></article>
        <article className="membership-status-card"><span>Orientation Status</span><strong>{membership?.orientation_status || "not_started"}</strong></article>
        <article className="membership-status-card"><span>Learning Streak</span><strong>{summary?.streak_days ?? 0} days</strong></article>
      </section>

      <main className="member-hub-grid">
        <section className="cosmic-section member-hub-card member-hub-card--wide">
          <h2>Continue Your Journey</h2>
          <div className="journey-list">
            <Link to="/library">Books & Audiobooks Library</Link>
            <Link to="/timeline">African Origins Timeline</Link>
            <Link to="/decolonize">30-Day Decolonization Portal</Link>
          </div>
        </section>

        <section className="cosmic-section member-hub-card">
          <h2>Swahili Word of the Day</h2>
          {swahiliWord ? <><p className="word-of-day">{swahiliWord.swahili}</p><p>{swahiliWord.english}</p><p className="timestamp">{swahiliWord.sentence || swahiliWord.example_swahili}</p><a href="/languages/swahili.html">Practice today’s Swahili lesson</a></> : <p>Swahili lesson content is being prepared.</p>}
        </section>

        <section className="cosmic-section member-hub-card">
          <h2>Historical Fact of the Day</h2>
          <p>{historicalFact || "A new historical highlight is being prepared."}</p>
        </section>

        <section className="cosmic-section member-hub-card">
          <h2>Community Activity</h2>
          {recentActivity.length === 0 ? <p>No tracked activity yet. Start a lesson, read a resource, or join a discussion.</p> : <ul className="activity-feed">{recentActivity.map((item, idx) => <li key={idx}><span className="highlight">{item.title || item.type}</span><div>{item.detail || item.description}</div></li>)}</ul>}
        </section>

        <section className="cosmic-section member-hub-card">
          <h2>Featured Resource</h2>
          <p className="highlight">{featuredTimeline?.title || "Forgotten Black Mega Cities"}</p>
          <p>{featuredTimeline?.summary || "Study historical examples of community development, trade, infrastructure, and institution building."}</p>
          <Link to="/library">Explore resource library</Link>
        </section>

        <section className="cosmic-section member-hub-card">
          <h2>Community Opportunities</h2>
          {testingOpportunities.length === 0 ? <p>Check back for testing circles, study groups, and builder calls.</p> : <ul>{testingOpportunities.map((opportunity) => <li key={opportunity}>{opportunity}</li>)}</ul>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--action">
          <h2>Today’s Action</h2>
          <p>Read one page, practice one word, and share one insight with the community.</p>
          <Link to="/library" className="member-action-btn">Start Now</Link>
        </section>
      </main>

      {communityUpdates.length > 0 ? <section className="cosmic-section"><h2>📣 Community Updates</h2><ul className="activity-feed">{communityUpdates.map((update) => <li key={update}>{update}</li>)}</ul></section> : null}

      {isBuilder ? <section className="cosmic-section builder-dashboard-section"><h2>🛠️ Builder Participation</h2><div className="builder-dashboard-grid"><article><h3>Contribution History</h3>{contributionHistory.length === 0 ? <p>No Builder contributions have been tracked yet.</p> : <ul>{contributionHistory.map((contribution) => <li key={contribution.id || contribution.title}>{contribution.title || contribution.summary}</li>)}</ul>}</article><article><h3>Feedback Participation</h3><p>{builder?.feedback_participation?.summary || "Builder feedback tracking is being prepared."}</p></article></div></section> : null}
    </div>
  );
}
