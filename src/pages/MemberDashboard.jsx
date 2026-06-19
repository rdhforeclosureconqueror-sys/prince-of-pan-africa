import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { getCommunityTrustExperience, getOpenVerificationRequests, getRecentCommunityActivity, getStarExperience } from "../api/participation";
import { getDailyHistoricalSpotlight } from "../data/dailyHistoricalSpotlights";
import { TIMELINE_A_AFRICA_ORIGINS } from "../data/timelineA_africaOrigins";
import swahiliLessons from "../../public/languages/swahili_30days.json";
import "../styles/dashboard.css";

const COMMUNITY_CHALLENGES = [
  {
    day: "Sunday",
    title: "Wellness Sunday",
    action: "Restore your body, mind, and spirit.",
    prompts: ["Fitness", "Nutrition", "Mental wellness", "Spiritual practice"],
  },
  {
    day: "Monday",
    title: "Black Business Monday",
    action: "Support a Black-owned business and prepare a receipt, review, or recommendation for the community.",
    prompts: ["Receipt", "Review", "Recommendation"],
  },
  {
    day: "Tuesday",
    title: "Member Spotlight Tuesday",
    action: "Highlight a community member whose discipline, service, or creativity deserves recognition.",
    prompts: ["Name the member", "Share the win", "Invite others to celebrate"],
  },
  {
    day: "Wednesday",
    title: "Wisdom Wednesday",
    action: "Share a teaching that sharpened your thinking this week.",
    prompts: ["Book insight", "Quote", "Proverb"],
  },
  {
    day: "Thursday",
    title: "Economic Power Thursday",
    action: "Join the economic power discussion and turn one idea into a practical next step.",
    prompts: ["Investing", "Business", "Real estate", "Cooperatives"],
  },
  {
    day: "Friday",
    title: "Family & Legacy Friday",
    action: "Document one lesson or practice that strengthens family continuity.",
    prompts: ["Parenting", "Traditions", "Family lessons"],
  },
  {
    day: "Saturday",
    title: "Community Service Saturday",
    action: "Show how you are helping your neighborhood, school, family, or local organization.",
    prompts: ["Volunteer", "Mentor", "Clean up", "Check on elders"],
  },
];

const LEARNING_PATHS = [
  { title: "Ancient African Science", reason: "Start the week by studying African innovation as a source of technical confidence." },
  { title: "Forgotten Black Mega Cities", reason: "Today’s mission points toward infrastructure, trade, and city-building memory." },
  { title: "Blackonomics", reason: "Economic support becomes stronger when daily spending connects to ownership and strategy." },
  { title: "Leadership Foundations", reason: "Community command requires members who can organize, listen, decide, and serve." },
  { title: "African Empires", reason: "Empire study restores a long view of governance, defense, diplomacy, and culture." },
  { title: "Swahili Foundations", reason: "Language practice builds cultural continuity one word at a time." },
];

function formatDate(date) {
  return date.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

export default function MemberDashboard() {
  const [overview, setOverview] = useState(null);
  const [activity, setActivity] = useState([]);
  const [starExperience, setStarExperience] = useState(null);
  const [communityTrust, setCommunityTrust] = useState(null);
  const [verificationRequests, setVerificationRequests] = useState([]);
  const [communityActivity, setCommunityActivity] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const refreshStarExperience = async () => {
      try {
        const starRes = await getStarExperience();
        if (mounted) setStarExperience(starRes || null);
      } catch (err) {
        console.warn("[participation] dashboard refresh failed", err);
      }
    };
    const onParticipationUpdated = (event) => {
      console.info("[participation] dashboard refresh", event.detail);
      if (event.detail) {
        setStarExperience((previous) => ({ ...(previous || {}), participation: event.detail.participation, history: [event.detail.activity, ...((previous?.history || []).filter((item) => item.id !== event.detail.activity?.id))] }));
      }
      refreshStarExperience();
    };
    window.addEventListener("simba:participation-updated", onParticipationUpdated);
    (async () => {
      try {
        const [overviewRes, activityRes, starRes, trustRes, verificationRes, communityActivityRes] = await Promise.all([
          api("/member/overview", { method: "GET" }),
          api("/member/activity", { method: "GET" }),
          getStarExperience(),
          getCommunityTrustExperience(),
          getOpenVerificationRequests(),
          getRecentCommunityActivity(),
        ]);

        if (!mounted) return;
        setOverview(overviewRes || null);
        setActivity(activityRes?.activity || activityRes?.items || []);
        setStarExperience(starRes || null);
        setCommunityTrust(trustRes?.community_trust || null);
        setVerificationRequests(verificationRes?.verification_requests || []);
        setCommunityActivity(communityActivityRes?.activity || []);
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
      window.removeEventListener("simba:participation-updated", onParticipationUpdated);
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
  const community = membership?.community || {};
  const communityOnboarding = community?.onboarding || {};
  const communityUpdates = Array.isArray(membership?.community_updates) ? membership.community_updates : [];
  const testingOpportunities = Array.isArray(builder?.testing_opportunities) ? builder.testing_opportunities : [];
  const contributionHistory = Array.isArray(builder?.contribution_history) ? builder.contribution_history : [];
  const builderActivation = builder?.activation || {};
  const isBuilder = Boolean(builder?.is_builder || membership?.type === "builder_member");
  const memberName = overview?.profile?.name || overview?.user?.name || overview?.user?.email || overview?.email || "Member";
  const swahiliDays = Array.isArray(swahiliLessons?.days) ? swahiliLessons.days : [];
  const swahiliLesson = swahiliDays.length ? swahiliDays[(dayOfYear - 1) % swahiliDays.length] : null;
  const swahiliWord = swahiliLesson?.words?.[0] || null;
  const dailySpotlight = getDailyHistoricalSpotlight(today);
  const featuredTimeline = TIMELINE_A_AFRICA_ORIGINS[dayOfYear % TIMELINE_A_AFRICA_ORIGINS.length];
  const todayChallenge = COMMUNITY_CHALLENGES[today.getDay()];
  const learningPath = LEARNING_PATHS[(dayOfYear - 1) % LEARNING_PATHS.length];
  const recentActivity = activity.slice(0, 5);
  const membershipStatusLabel = membership?.status === "active"
    ? "Active paid membership"
    : "Free access · payment not confirmed";
  const historicalSpotlightTitle = dailySpotlight?.title || featuredTimeline?.title || "Historical spotlight is being prepared.";
  const historicalSpotlightContext = dailySpotlight?.historical_context || featuredTimeline?.summary || "The current source dataset has a short entry for this date. Treat this card as a launch point for deeper timeline study.";
  const participation = starExperience?.participation || overview?.participation || {};
  const currentStar = participation?.star ?? summary?.star ?? 0;
  const participationScore = participation?.participation_score ?? summary?.participation_score ?? 0;
  const currentRank = participation?.current_rank ?? summary?.current_rank ?? "Registered User";
  const activityCount = participation?.activities_completed ?? participation?.activity_count ?? summary?.activity_count ?? 0;
  const currentStreak = participation?.current_streak ?? summary?.streak_days ?? 0;
  const rankProgress = participation?.rank_progress || {};
  const starOpportunities = starExperience?.opportunities || [];
  const starHistory = starExperience?.history || activity || [];
  const starRewards = starExperience?.rewards || [];
  const leaderboards = starExperience?.leaderboards || {};
  const trust = communityTrust || {};
  const trustProgress = trust.progress || {};
  const trustPercent = Math.min(100, trust.trust_percent ?? trust.trust_score ?? 0);
  const trustLadder = trustProgress.levels || [];
  const recentCommunityActivity = communityActivity.length ? communityActivity : [];
  const impactStats = [
    ["Businesses Supported This Month", summary?.businesses_supported_month ?? 0],
    ["Books Completed", summary?.books_completed ?? 0],
    ["Lessons Completed", summary?.lessons_completed ?? summary?.activity_count ?? 0],
    ["Community Challenges Completed", summary?.community_challenges_completed ?? 0],
    ["Members Participating", summary?.members_participating ?? 0],
    ["Hours Served", summary?.hours_served ?? 0],
  ];

  if (loading) return <div className="admin-loading">Loading your dashboard...</div>;
  if (error) return <div className="admin-error">⚠️ {error}</div>;

  return (
    <div className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Today’s Mission</p>
        <h1>Welcome Back, {memberName}</h1>
        <p className="subtitle">Daily launch sequence for learning, participation, economic support, leadership, and restoration.</p>
        <div className="mission-status-strip">
          <span>{membership?.label || "Free Member"}</span>
          <span>{membershipStatusLabel}</span>
          <span>{formatDate(today)}</span>
        </div>
        <div className="participation-pulse" aria-label="Participation Engine summary">
          <article><span>Current STAR</span><strong>{currentStar}</strong></article>
          <article><span>Participation Score</span><strong>{participationScore}</strong></article>
          <article><span>Community Rank</span><strong>{currentRank}</strong></article>
          <article><span>Activities Recorded</span><strong>{activityCount}</strong></article>
        </div>
        <section className="star-credits-card" aria-label="STAR Community Credits">
          <div>
            <p className="member-kicker">STAR Community Credits</p>
            <h2>{currentStar} STAR</h2>
            <p>{currentRank} · {currentStreak} day streak · {activityCount} activities completed</p>
          </div>
          <div className="star-rank-progress">
            <span>Progress to {rankProgress.next_rank || "next rank"}</span>
            <strong>{rankProgress.percent ?? 0}%</strong>
            <div className="star-progress-track"><i style={{ width: `${rankProgress.percent ?? 0}%` }} /></div>
            <small>{rankProgress.star_to_next_rank ?? 0} STAR to next rank</small>
          </div>
        </section>
        <div className="daily-actions-panel" aria-label="Today’s Four Actions">
          <h2>Today’s Four Actions</h2>
          <label><input type="checkbox" readOnly /> Learn Today’s Swahili Word</label>
          <label><input type="checkbox" readOnly /> Read Today’s Historical Spotlight</label>
          <label><input type="checkbox" readOnly /> Complete Today’s Community Challenge</label>
          <label><input type="checkbox" readOnly /> Share One Insight</label>
          <strong>Daily Progress: 0/4</strong>
        </div>
      </header>

      <main className="member-hub-grid command-grid">

        <section className="cosmic-section member-hub-card member-hub-card--wide community-trust-card" aria-label="Community Trust">
          <p className="section-kicker">Community Labor Exchange</p>
          <div className="community-trust-header">
            <div>
              <h2>Community Trust</h2>
              <p>Community Trust grows when you complete verified contributions, help verify others, and participate consistently.</p>
            </div>
            <strong className="trust-badge">{trust.leadership_level || "Community Member"}</strong>
          </div>
          <div className="trust-score-layout">
            <article className="trust-score-card"><span>Trust Score</span><strong>{trustPercent}%</strong><div className="star-progress-track"><i style={{ width: `${trustPercent}%` }} /></div></article>
            <article><span>STAR Community Credits</span><strong>{currentStar}</strong><small>Rewards for participation</small></article>
            <article><span>Verified Contributions</span><strong>{trust.verified_contributions ?? 0}</strong></article>
            <article><span>Verifications Completed</span><strong>{trust.verifications_completed ?? 0}</strong></article>
            <article><span>Verification Accuracy</span><strong>{trust.verification_accuracy ?? 100}%</strong></article>
            <article><span>Consistency Streak</span><strong>{trust.consistency_streak ?? 0} Days</strong></article>
          </div>
          <div className="trust-next-level"><span>Next Level: {trust.next_level || "Verified Contributor"}</span><strong>{trustProgress.percent ?? 0}%</strong></div>
          <div className="star-progress-track"><i style={{ width: `${trustProgress.percent ?? 0}%` }} /></div>
          <div className="trust-ladder" aria-label="Community Trust ladder">{trustLadder.map((level) => <span key={level.level} className={(trust.trust_score ?? 0) >= level.threshold ? "is-active" : ""}>{level.level}</span>)}</div>
          <ul className="trust-calculation-list">{(trust.calculation || []).map((line) => <li key={line}>{line}</li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide verification-requests-card">
          <p className="section-kicker">Help Verify Community Work</p>
          <h2>Pending Verification Opportunities</h2>
          {verificationRequests.length === 0 ? <p>No verification requests are open right now. When members submit proof of community work, you can help verify and earn STAR.</p> : <div className="verification-request-grid">{verificationRequests.map((request) => <article key={request.activity_id}><h3>{request.labor_category}</h3><p><strong>Submitted by:</strong> {request.submitted_by}</p><p><strong>Content/activity:</strong> {request.content || request.activity_type}</p><p><strong>Status:</strong> {request.status}</p><p><strong>Confirmations:</strong> {request.current_confirmations}/{request.required_confirmations}</p><strong className="star-reward-label">+{request.star_reward} STAR for verification</strong></article>)}</div>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide community-activity-card">
          <p className="section-kicker">Recent Community Labor Activity</p>
          <h2>Community Activity</h2>
          {recentCommunityActivity.length === 0 ? <p>Community labor activity will appear here as members learn, submit proof, and verify one another.</p> : <ul className="activity-feed">{recentCommunityActivity.map((item) => <li key={item.id}><span className="highlight">{item.message}</span><div>{item.timestamp ? new Date(item.timestamp).toLocaleDateString() : "Recently"} · {item.status} · +{item.star_award || 0} STAR</div></li>)}</ul>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide star-opportunities-card">
          <p className="section-kicker">STAR Engine</p>
          <h2>Today’s STAR Opportunities</h2>
          <div className="star-opportunity-grid">{starOpportunities.map((item) => <a key={item.activity_type} href={item.href} className="star-opportunity"><span>{item.title}</span><strong>+{item.star} STAR</strong></a>)}</div>
        </section>

        <section className="cosmic-section member-hub-card star-history-card">
          <p className="section-kicker">Verified Timeline</p>
          <h2>Activity History</h2>
          {starHistory.length === 0 ? <p>No STAR activity yet. Complete an opportunity to begin.</p> : <ul className="star-timeline">{starHistory.slice(0, 8).map((item) => <li key={item.activity_id || item.id}><strong>{(item.activity_type || item.title || "Activity").replaceAll("_", " ")}</strong><span>{item.timestamp ? new Date(item.timestamp).toLocaleDateString() : "Today"} · +{item.star_award || 0} STAR · {item.verification_status || "recorded"}</span></li>)}</ul>}
        </section>

        <section className="cosmic-section member-hub-card star-rewards-card">
          <p className="section-kicker">Community Benefits</p>
          <h2>STAR Rewards</h2>
          <ul className="star-reward-list">{starRewards.map((reward) => <li key={reward.title} className={reward.unlocked ? "is-unlocked" : ""}><span>{reward.title}</span><strong>{reward.unlocked ? "Unlocked" : `${reward.star_needed} STAR needed`}</strong></li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card star-leaderboard-card">
          <p className="section-kicker">Celebration Board</p>
          <h2>Community Leaderboards</h2>
          <div className="star-leaderboard-grid">{Object.entries(leaderboards).map(([name, rows]) => <article key={name}><h3>{name.replaceAll("_", " ")}</h3>{rows?.length ? rows.slice(0, 3).map((row, idx) => <p key={`${name}-${row.user_id}`}>#{idx + 1} Member {row.user_id}: {row.star} STAR</p>) : <p>Be the first this week.</p>}</article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card swahili-command-card">
          <p className="section-kicker">Section 2</p>
          <h2>Swahili Word of the Day</h2>
          {swahiliWord ? <><p className="word-of-day">{swahiliWord.swahili}</p><dl className="data-list"><dt>Pronunciation</dt><dd>{swahiliWord.pronunciation || "Practice aloud with the lesson audio."}</dd><dt>Definition</dt><dd>{swahiliWord.english}</dd><dt>Example</dt><dd>{swahiliWord.sentence || swahiliWord.example_swahili}</dd><dt>Why it matters culturally</dt><dd>{swahiliLesson?.culture || swahiliLesson?.tip || "Swahili connects millions across East Africa and helps members practice restoration through language."}</dd></dl><a href="/languages/swahili.html" className="member-action-btn">Practice Word</a></> : <p>Swahili lesson content is being prepared.</p>}
        </section>

        <section className="cosmic-section member-hub-card history-command-card">
          <p className="section-kicker">Section 3</p>
          <h2>African History Spotlight</h2>
          <p className="history-date">{formatDate(today)}</p>
          <p className="highlight">{historicalSpotlightTitle}</p>
          <dl className="data-list"><dt>Did you know?</dt><dd>{dailySpotlight?.did_you_know || historicalSpotlightTitle}</dd><dt>Context</dt><dd>{historicalSpotlightContext}</dd><dt>Key people or places</dt><dd>{dailySpotlight?.key_people_or_places || "Study the leaders, institutions, and communities behind the moment—not just the headline."}</dd><dt>Category</dt><dd>{dailySpotlight?.category || "African and Black history"}</dd><dt>Why it matters today</dt><dd>{dailySpotlight?.why_it_matters_today || "Use the lesson to guide today’s leadership, economic choices, and community restoration."}</dd><dt>Reflection question</dt><dd>{dailySpotlight?.reflection_question || "What responsibility does this history place on my actions today?"}</dd></dl>
          <p className="data-note">Source note: {dailySpotlight?.source_note || "Repo timeline fallback; richer daily entries are being expanded."}</p>
          <Link to="/timeline" className="member-action-btn member-action-btn--secondary">Learn More</Link>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide challenge-command-card">
          <p className="section-kicker">Section 4</p>
          <h2>Community Challenge of the Day</h2>
          <div className="challenge-layout"><div><p className="challenge-day">{todayChallenge.day}</p><h3>{todayChallenge.title}</h3><p>{todayChallenge.action}</p><p className="data-note">Discord bridge pending: complete the action now and save your post text for the community feed.</p></div><ul className="command-chip-list">{todayChallenge.prompts.map((prompt) => <li key={prompt}>{prompt}</li>)}</ul></div>
          <a href="#community-feed" className="member-action-btn">Prepare Community Share</a>
        </section>

        <section className="cosmic-section member-hub-card impact-command-card">
          <p className="section-kicker">Section 5</p>
          <h2>Community Impact</h2>
          <p className="data-note">Tracked from current in-app records. Zero means the metric is not recorded yet—not that the community has no impact.</p>
          <div className="impact-grid">{impactStats.map(([label, value]) => <article key={label}><strong>{value}</strong><span>{label}</span></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card learning-path-card">
          <p className="section-kicker">Section 6</p>
          <h2>Today’s Learning Path</h2>
          <p className="highlight">{learningPath.title}</p><p>{featuredTimeline?.summary || "Study a focused pathway that turns knowledge into daily practice."}</p><p><strong>Why am I seeing this today?</strong> {learningPath.reason}</p><Link to="/library" className="member-action-btn member-action-btn--secondary">Open Learning Path</Link>
        </section>

        <section className="cosmic-section member-hub-card assessment-center-card">
          <p className="section-kicker">Continue Your Journey</p>
          <h2>Assessment Center</h2>
          <p>Take a Simba assessment, receive recommendations, and let STAR rewards process automatically when eligible.</p>
          <Link to="/assessments" className="member-action-btn">Open Assessment Center</Link>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide feed-command-card" id="community-feed">
          <p className="section-kicker">Section 7</p>
          <h2>Community Feed</h2>
          {recentActivity.length === 0 ? <ul className="activity-feed"><li><span className="highlight">Member wins</span><div>Share your first win to activate the feed.</div></li><li><span className="highlight">Business spotlights</span><div>Post a recommendation from today’s challenge.</div></li><li><span className="highlight">Builder announcements</span><div>Builder updates will appear here as the Discord bridge expands.</div></li><li><span className="highlight">New books & audiobooks</span><div>Library additions will be routed into this mission feed.</div></li></ul> : <ul className="activity-feed">{recentActivity.map((item, idx) => <li key={item.id || idx}><span className="highlight">{item.title || item.type}</span><div>{item.detail || item.description}</div></li>)}</ul>}
        </section>
      </main>

      {membership?.type === "community_member" && !community?.community_onboarding_completed ? <section className="cosmic-section builder-dashboard-section"><h2>🌱 Community Member First 5 Minutes</h2><p>Start with a simple path: choose interests, choose a first learning path, prepare for Discord, and complete one daily mission.</p><Link to="/community/onboarding" className="member-action-btn member-action-btn--secondary">Start Community Onboarding</Link></section> : null}

      {community?.community_onboarding_completed ? <section className="cosmic-section builder-dashboard-section"><h2>🌱 Community Onboarding</h2><div className="builder-dashboard-grid"><article><h3>First Start Completed</h3><p><strong>Learning path:</strong> {communityOnboarding.selected_learning_path || "Not selected"}</p><p><strong>First daily mission:</strong> {community?.first_daily_mission_completed ? "Completed" : "Not completed"}</p></article><article><h3>Learning Interests</h3><p>{Array.isArray(communityOnboarding.selected_interests) && communityOnboarding.selected_interests.length ? communityOnboarding.selected_interests.join(" · ") : "No interests selected yet."}</p></article></div></section> : null}

      {communityUpdates.length > 0 ? <section className="cosmic-section"><h2>📡 Command Updates</h2><ul className="activity-feed">{communityUpdates.map((update) => <li key={update}>{update}</li>)}</ul></section> : null}

      {isBuilder ? <section className="cosmic-section builder-dashboard-section"><h2>🛠️ Builder Participation</h2><div className="builder-dashboard-grid"><article><h3>Activation State</h3><p><strong>Builder level:</strong> {builder?.builder_level || "not_started"}</p><p><strong>Onboarding completed:</strong> {builder?.onboarding_completed ? "Yes" : "No"}</p><p><strong>First challenge completed:</strong> {builder?.first_challenge_completed ? "Yes" : "No"}</p><p><strong>First contribution completed:</strong> {builder?.first_contribution_completed ? "Yes" : "No"}</p>{builder?.onboarding_completed ? <p>Your activation is recorded. Use the dashboard to continue participating.</p> : <Link to="/builder/onboarding" className="member-action-btn member-action-btn--secondary">Continue Builder Activation</Link>}</article><article><h3>Selected Builder Lane</h3><p>{builderActivation.team || "Choose a Builder team during activation."}</p><p>{Array.isArray(builderActivation.interests) && builderActivation.interests.length ? builderActivation.interests.join(" · ") : "Interests are not selected yet."}</p></article><article><h3>Contribution History</h3>{contributionHistory.length === 0 ? <p>No Builder contributions have been tracked yet.</p> : <ul>{contributionHistory.map((contribution) => <li key={contribution.id || contribution.title}>{contribution.title || contribution.summary}</li>)}</ul>}</article><article><h3>Feedback Participation</h3><p>{builder?.feedback_participation?.summary || "Builder feedback tracking is being prepared."}</p></article><article><h3>Testing Opportunities</h3>{testingOpportunities.length === 0 ? <p>No builder tests are open today.</p> : <ul>{testingOpportunities.map((opportunity) => <li key={opportunity}>{opportunity}</li>)}</ul>}</article></div></section> : null}
    </div>
  );
}
