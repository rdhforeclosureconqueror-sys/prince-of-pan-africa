import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { getStarExperience } from "../api/participation";
import "../styles/dashboard.css";
import "../styles/star-rewards.css";

const STAR_CATEGORIES = [
  { title: "Learning", detail: "Books, audiobook study, lessons, quizzes, and knowledge practice." },
  { title: "Preparedness", detail: "Approved household readiness, training, supplies, and resilience actions." },
  { title: "Service", detail: "Verified volunteer work, community help, event participation, and support actions." },
  { title: "Contribution", detail: "Builder participation, resource sharing, referrals, and cooperative contribution signals." },
];

const STAR_RULES = [
  "STAR measures participation, learning, service, and contribution.",
  "STAR is not money.",
  "STAR is not cash.",
  "STAR is not ownership.",
  "STAR cannot be bought or purchased.",
  "STAR cannot be sold.",
  "STAR cannot be transferred.",
  "STAR cannot be redeemed for cash.",
  "STAR does not automatically create owner-member status.",
];

function displayLabel(value, fallback = "STAR activity") {
  return String(value || fallback).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function activityTime(item) {
  return item?.created_at || item?.completed_at || item?.timestamp || item?.date || "";
}

function isHighValueOrVerificationActivity(item) {
  const type = String(item?.activity_type || item?.type || item?.title || "").toLowerCase();
  const status = String(item?.verification_status || item?.status || item?.review_status || "").toLowerCase();
  const starAward = Number(item?.star_award ?? item?.star ?? item?.amount ?? 0);
  return starAward >= 15 || /verif|review|appeal|reversal|volunteer|referr|support|service/.test(type) || /pending|review|verified|rejected|appeal/.test(status);
}

function groupedActivityTitle(item) {
  const label = displayLabel(item.activity_type || item.type || item.title);
  if (item.count > 1) return `${item.count} ${label.toLowerCase()} actions`;
  return item.title || label;
}

function groupRepeatedActivity(items = []) {
  const grouped = new Map();
  const visible = [];
  items.forEach((item, index) => {
    if (isHighValueOrVerificationActivity(item)) {
      visible.push({ ...item, count: 1, latest: activityTime(item), groupKey: `visible:${item?.id || index}` });
      return;
    }
    const type = item?.activity_type || item?.type || item?.title || "STAR activity";
    const source = item?.source_module || item?.module || "simba";
    const date = activityTime(item).slice(0, 10) || "undated";
    const key = `${type}:${source}:${date}`;
    const current = grouped.get(key) || { ...item, count: 0, star_award: 0, latest: activityTime(item), groupKey: key };
    current.count += 1;
    current.star_award += Number(item?.star_award ?? item?.star ?? item?.amount ?? 0);
    if (activityTime(item) > current.latest) current.latest = activityTime(item);
    grouped.set(key, current);
  });
  return [...visible, ...Array.from(grouped.values())].sort((a, b) => String(b.latest || activityTime(b)).localeCompare(String(a.latest || activityTime(a)))).slice(0, 8);
}

function calculateWeeklyStar(items = []) {
  const now = new Date();
  const weekAgo = new Date(now);
  weekAgo.setDate(now.getDate() - 7);
  return items.reduce((total, item) => {
    const when = activityTime(item) ? new Date(activityTime(item)) : null;
    if (!when || Number.isNaN(when.getTime()) || when < weekAgo) return total;
    return total + Number(item?.star_award ?? item?.star ?? item?.amount ?? 0);
  }, 0);
}

export default function StarRewardsPage() {
  const [overview, setOverview] = useState(null);
  const [activity, setActivity] = useState([]);
  const [starExperience, setStarExperience] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [overviewRes, activityRes, starRes] = await Promise.allSettled([
          api("/member/overview", { method: "GET" }),
          api("/member/activity", { method: "GET" }),
          getStarExperience(),
        ]);
        if (!mounted) return;
        if (overviewRes.status === "fulfilled") setOverview(overviewRes.value || null);
        if (activityRes.status === "fulfilled") setActivity(activityRes.value?.activity || activityRes.value?.items || []);
        if (starRes.status === "fulfilled") setStarExperience(starRes.value || null);
        const firstFailure = [overviewRes, activityRes, starRes].find((result) => result.status === "rejected");
        if (firstFailure && overviewRes.status !== "fulfilled" && starRes.status !== "fulfilled") {
          setError(firstFailure.reason?.status === 401 ? "Sign in to view your personal STAR balance and activity." : "STAR data is not available yet. Safe empty states are shown below.");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const participation = starExperience?.participation || overview?.participation || {};
  const summary = overview?.summary_stats || overview || {};
  const starHistory = useMemo(() => starExperience?.history?.length ? starExperience.history : activity, [starExperience, activity]);
  const groupedActivity = useMemo(() => groupRepeatedActivity(starHistory), [starHistory]);
  const currentStar = participation?.star ?? summary?.star ?? 0;
  const earnedThisWeek = participation?.star_earned_this_week ?? participation?.weekly_star ?? summary?.star_earned_this_week ?? calculateWeeklyStar(starHistory);
  const rewards = Array.isArray(starExperience?.rewards) ? starExperience.rewards : [];
  const badges = rewards.filter((reward) => reward.unlocked).slice(0, 6);
  const opportunities = Array.isArray(starExperience?.opportunities) ? starExperience.opportunities : [];

  return (
    <main className="admin-dashboard star-rewards-page cosmic-readable-shell">
      <header className="dashboard-header star-rewards-hero">
        <p className="section-kicker">STAR Rewards</p>
        <h1>Participation recognition, safely separated.</h1>
        <p className="subtitle">Track STAR earned through approved learning, preparedness, service, and contribution actions using existing Simba participation data.</p>
        <div className="star-hero-actions">
          <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Member Home</Link>
          <Link to="/applications" className="member-action-btn">View Applications</Link>
        </div>
      </header>

      {loading ? <div className="admin-loading">Loading STAR participation recognition from existing activity data...</div> : null}
      {error ? <section className="cosmic-section star-safe-notice"><strong>{error}</strong></section> : null}

      <section className="star-summary-grid" aria-label="STAR summary">
        <article><span>Member STAR Balance</span><strong>{Number(currentStar).toLocaleString()}</strong><small>Calculated from existing STAR participation summary data.</small></article>
        <article><span>STAR Earned This Week</span><strong>{Number(earnedThisWeek || 0).toLocaleString()}</strong><small>{earnedThisWeek ? "Based on available recent activity timestamps." : "No weekly STAR activity is available yet."}</small></article>
        <article><span>Participation Rank</span><strong>{participation?.current_rank || summary?.current_rank || "Beginning"}</strong><small>{participation?.activities_completed ?? participation?.activity_count ?? summary?.activity_count ?? 0} recorded activities</small></article>
      </section>

      <section className="cosmic-section star-rules-card">
        <p className="section-kicker">Integrity Rules</p>
        <h2>What STAR means — and what it does not mean</h2>
        <ul>{STAR_RULES.map((rule) => <li key={rule}>{rule}</li>)}</ul>
      </section>

      <section className="star-content-grid">
        <div className="cosmic-section">
          <p className="section-kicker">STAR Categories</p>
          <h2>How STAR is organized</h2>
          <div className="star-category-grid">{STAR_CATEGORIES.map((category) => <article key={category.title}><strong>{category.title}</strong><p>{category.detail}</p></article>)}</div>
        </div>

        <div className="cosmic-section">
          <p className="section-kicker">How STAR is earned</p>
          <h2>Approved participation actions</h2>
          {opportunities.length ? <ul className="star-list">{opportunities.slice(0, 8).map((item) => <li key={item.activity_type || item.title}><strong>{item.title || displayLabel(item.activity_type)}</strong><span>{item.description || item.source_module || "Participation opportunity"}</span>{item.star ? <small>+{item.star} STAR</small> : null}</li>)}</ul> : <p>No earning opportunities are available yet. Complete approved learning, preparedness, service, or contribution actions to begin earning STAR.</p>}
        </div>
      </section>

      <section className="cosmic-section">
        <p className="section-kicker">Recent STAR Activity</p>
        <h2>Existing activity only</h2>
        {groupedActivity.length ? <div className="activity-scroll">{groupedActivity.map((item) => <article key={item.groupKey || `${item.activity_type || item.title}-${item.latest || item.id}`} className="activity-card activity-card--feed"><span>{displayLabel(item.activity_type || item.type || item.title)}</span><strong>{groupedActivityTitle(item)}</strong><p>{item.count > 1 ? "Similar low-risk participation actions from the same day are grouped to keep this feed readable." : (item.description || item.source_module || item.module || "Recorded Simba participation activity.")}</p><small>{Number(item.star_award || 0) ? `+${Number(item.star_award).toLocaleString()} STAR participation recognition · not money, cash, ownership, transferable, or redeemable for cash` : "STAR amount not shown · STAR is participation recognition only"}</small></article>)}</div> : <p>No STAR activity yet. Members can earn STAR participation recognition through approved learning, reflection, preparedness, sharing, service, building, and support actions. STAR is not money, cash, ownership, transferable, or redeemable for cash, and it does not automatically create owner-member status.</p>}
      </section>

      <section className="cosmic-section">
        <p className="section-kicker">Milestones and Badges</p>
        <h2>Recognition already available</h2>
        {badges.length ? <div className="achievement-gallery">{badges.map((badge) => <article key={badge.title} className="is-earned"><span>🏆</span><strong>{badge.title}</strong><small>{badge.description || `${badge.star_needed || currentStar} STAR milestone`}</small></article>)}</div> : <p>No STAR milestones or badges are available yet. Keep participating to unlock recognition when existing data supports it.</p>}
      </section>
    </main>
  );
}
