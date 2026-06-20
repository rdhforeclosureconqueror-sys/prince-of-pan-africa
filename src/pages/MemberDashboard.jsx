import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { getAssessmentResults, getGrowthProfile } from "../api/assessments";
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

function normalizeAssessmentText(value) {
  return String(value || "").toLowerCase().replace(/[\s_]+/g, "-").replace(/[^a-z0-9-]/g, "");
}

const ASSESSMENT_GROUPS = [
  { key: "business-owner-assessment", terms: ["business-owner-assessment", "business-assessment", "business-owner"] },
  { key: "customer-voice-of-customer", terms: ["customer-voice-of-customer", "voice-of-customer", "customer-assessment", "voc"] },
  { key: "love-archetype-engine", terms: ["love-archetype-engine", "love-engine", "love-archetype"] },
  { key: "leadership-archetype-engine", terms: ["leadership-archetype-engine", "leadership-engine", "leadership-archetype"] },
  { key: "loyalty-archetype-engine", terms: ["loyalty-archetype-engine", "loyalty-engine", "loyalty-archetype"] },
  { key: "youth-rite-of-passage", terms: ["youth-rite-of-passage", "rite-of-passage", "gates"] },
  { key: "k-6-assessment-mvp", terms: ["k-6-assessment-mvp", "k6-assessment-mvp", "k-6", "k6"] },
];

function assessmentGroupKey(item) {
  const raw = [item?.assessment_id, item?.assessment_type, item?.assessment_name, item?.category, item?.slug, item?.id]
    .filter(Boolean)
    .map(normalizeAssessmentText)
    .join(" ");
  const match = ASSESSMENT_GROUPS.find((group) => group.terms.some((term) => raw.includes(normalizeAssessmentText(term))));
  return match?.key || normalizeAssessmentText(item?.assessment_id || item?.assessment_type || item?.assessment_name || item?.category || "garvey-assessment");
}

function assessmentTime(item) {
  return item?.completed_at || item?.completion_date || item?.created_at || "";
}

function sortAssessmentsByTime(a, b) {
  return assessmentTime(b).localeCompare(assessmentTime(a));
}

function latestCompletedAssessments(results) {
  const grouped = new Map();
  results
    .filter((item) => item?.completion_status === "completed" || item?.completed_at)
    .forEach((item) => {
      const key = item.assessment_group_key || assessmentGroupKey(item);
      grouped.set(key, [...(grouped.get(key) || []), item]);
    });

  return Array.from(grouped.entries())
    .map(([key, attempts]) => {
      const sortedAttempts = [...attempts].sort(sortAssessmentsByTime);
      return { ...sortedAttempts[0], assessment_group_key: key, attempt_count: sortedAttempts.length, attempt_history: sortedAttempts };
    })
    .sort(sortAssessmentsByTime);
}

function resultLabel(item) {
  if (typeof item?.primary_result === "string") return item.primary_result;
  return item?.primary_result?.label || item?.primary_result?.name || item?.archetype?.name || item?.archetype?.label || item?.overall_score || "Saved";
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
  const [growthProfile, setGrowthProfile] = useState(null);
  const [assessmentResults, setAssessmentResults] = useState([]);
  const [latestAssessmentResults, setLatestAssessmentResults] = useState([]);

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
        const [overviewRes, activityRes, starRes, trustRes, verificationRes, communityActivityRes, growthRes, assessmentResultsRes] = await Promise.all([
          api("/member/overview", { method: "GET" }),
          api("/member/activity", { method: "GET" }),
          getStarExperience(),
          getCommunityTrustExperience(),
          getOpenVerificationRequests(),
          getRecentCommunityActivity(),
          getGrowthProfile(),
          getAssessmentResults(),
        ]);

        if (!mounted) return;
        setOverview(overviewRes || null);
        setActivity(activityRes?.activity || activityRes?.items || []);
        setStarExperience(starRes || null);
        setCommunityTrust(trustRes?.community_trust || null);
        setVerificationRequests(verificationRes?.verification_requests || []);
        setCommunityActivity(communityActivityRes?.activity || []);
        setGrowthProfile(growthRes?.growth_profile || null);
        const allResults = Array.isArray(assessmentResultsRes?.results) ? assessmentResultsRes.results : [];
        setAssessmentResults(allResults);
        setLatestAssessmentResults(Array.isArray(assessmentResultsRes?.latest_results) ? assessmentResultsRes.latest_results : latestCompletedAssessments(allResults));
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
  const growthSummary = growthProfile?.summary || {};
  const growthBadges = Array.isArray(growthProfile?.badges) ? growthProfile.badges : [];
  const growthTimeline = Array.isArray(growthProfile?.timeline) ? growthProfile.timeline : [];
  const completedAssessments = latestAssessmentResults.length ? latestAssessmentResults : latestCompletedAssessments(assessmentResults);

  const latestAssessment = completedAssessments[0] || growthTimeline[0] || null;
  const latestAssessmentName = latestAssessment?.assessment_name || latestAssessment?.title || "No assessment completed yet";
  const latestAssessmentDate = latestAssessment?.completed_at || latestAssessment?.completion_date || null;
  const recommendedAssessment = growthSummary.recommended_next_assessment?.assessment_name || latestAssessment?.recommended_next_assessment?.assessment_name || "Open the Assessment Center";
  const currentStage = growthSummary.completed_assessments > 0 ? `${growthSummary.completed_assessments} assessment${growthSummary.completed_assessments === 1 ? "" : "s"} completed` : completedAssessments.length ? `${completedAssessments.length} assessment${completedAssessments.length === 1 ? "" : "s"} completed` : "Beginning the journey";
  const currentGrowthFocus = latestAssessment?.opportunities_for_growth?.[0] || latestAssessment?.category || growthSummary.recommended_next_assessment?.reason || "Complete your next Garvey assessment to reveal your focus.";
  const currentFocusTitle = completedAssessments.length ? "Developing Leadership Through Self-Awareness" : "Beginning Your Growth Journey";
  const currentFocusDescription = completedAssessments.length
    ? `Based on your most recent assessment, continue strengthening your leadership style by completing ${recommendedAssessment}.`
    : "Start with one Garvey assessment so Simba can reflect your progress back to you without inventing new scores.";
  const recentAchievement = growthBadges[0]?.label || (completedAssessments.length ? `Completed ${latestAssessmentName}` : "Your first achievement will appear after your first completed assessment.");
  const missionItems = [
    learningPath ? `Read or study one section from ${learningPath.title}.` : "Read one chapter from the community library.",
    swahiliWord ? `Practice today's Swahili word: ${swahiliWord.swahili}.` : "Complete one learning activity.",
    todayChallenge?.action || "Invite one community member into a constructive conversation.",
    `Earn ${starOpportunities[0]?.star || 25} STAR through one meaningful action today.`,
  ];
  const recentGrowthItems = [
    completedAssessments.length ? `Completed ${latestAssessmentName}` : "Assessment journey ready to begin",
    currentStar ? `Earned ${currentStar} total STAR` : "STAR rewards ready for your first action",
    growthBadges[0]?.label ? `New badge earned: ${growthBadges[0].label}` : "Badge path prepared",
    completedAssessments.length ? "Assessment synced" : "Garvey sync ready",
    "Growth journey updated",
  ];
  const journeyTimelineItems = [
    { label: "Joined Simba", detail: membershipStatusLabel, state: "complete" },
    ...completedAssessments.slice().reverse().map((item) => ({ label: `Completed ${item.assessment_name || item.title || "Garvey Assessment"}`, detail: resultLabel(item), state: "complete" })),
    currentStar > 0 ? { label: "Earned First STAR Reward", detail: `${currentStar} STAR currently available`, state: "complete" } : { label: "Earn First STAR Reward", detail: "Complete one daily mission or community action", state: "next" },
    { label: "Current Growth Focus", detail: currentFocusTitle, state: "current" },
    { label: "Next Recommended Assessment", detail: recommendedAssessment, state: "next" },
    { label: "Future Community Characteristics", detail: "Coming soon", state: "future" },
    { label: "Future Community Archetypes", detail: "Coming soon", state: "future" },
    { label: "Future Community Contribution", detail: "Coming soon", state: "future" },
  ];
  const latestReward = starRewards.find((reward) => reward.unlocked)?.title || starHistory[0]?.title || starHistory[0]?.activity_type?.replaceAll("_", " ") || "No reward unlocked yet";
  const nextReward = starRewards.find((reward) => !reward.unlocked);
  const nextRewardGoal = nextReward ? `${nextReward.title} · ${nextReward.star_needed} STAR needed` : rankProgress.next_rank ? `${rankProgress.next_rank} · ${rankProgress.star_to_next_rank ?? 0} STAR to go` : "Keep participating to unlock the next milestone";
  const greeting = today.getHours() < 12 ? "Good Morning" : today.getHours() < 18 ? "Good Afternoon" : "Good Evening";

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
    <div className="admin-dashboard member-launchpad living-dashboard command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header living-hero">
        <p className="member-kicker">Simba Community Operating System</p>
        <h1>{greeting}, {memberName}.</h1>
        <p className="subtitle">Every step you take strengthens both yourself and your community.</p>
        <div className="living-hero-grid" aria-label="Member journey summary">
          <article><span>Community Progress</span><strong>{participationScore}</strong><small>{currentRank}</small></article>
          <article><span>Current Journey</span><strong>{currentStage}</strong><small>{membership?.label || "Member"}</small></article>
          <article><span>Today’s Recommendation</span><strong>{recommendedAssessment}</strong><small>{currentGrowthFocus}</small></article>
          <article><span>Current STAR Balance</span><strong>{currentStar}</strong><small>{currentStreak} day streak</small></article>
        </div>
      </header>

      <main className="member-hub-grid living-dashboard-grid command-grid">
        <section className="cosmic-section member-hub-card member-hub-card--wide living-section growth-journey-card">
          <div className="section-heading-row">
            <div><p className="section-kicker">Your Growth Journey</p><h2>Where you are and where you are going</h2></div>
            <Link to="/assessments" className="member-action-btn member-action-btn--secondary">Open Assessment Center</Link>
          </div>
          <div className="journey-summary-grid">
            <article><span>Where You Are</span><strong>{currentStage}</strong><small>{membership?.label || "Member journey"}</small></article>
            <article><span>What You’ve Accomplished</span><strong>{recentAchievement}</strong><small>{completedAssessments.length} assessment milestone{completedAssessments.length === 1 ? "" : "s"}</small></article>
            <article><span>What Comes Next</span><strong>{recommendedAssessment}</strong><small>Continue the official Garvey path</small></article>
          </div>
          <ol className="living-journey-timeline" aria-label="Living community journey timeline">
            {journeyTimelineItems.map((item, index) => <li key={`${item.label}-${index}`} className={`journey-timeline-item journey-timeline-item--${item.state}`}><span className="journey-node">{item.state === "complete" ? "✓" : item.state === "current" ? "●" : "→"}</span><div><strong>{item.label}</strong><p>{item.detail}</p></div></li>)}
          </ol>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section current-focus-card">
          <div>
            <p className="section-kicker">Current Focus</p>
            <h2>{currentFocusTitle}</h2>
            <p>{currentFocusDescription}</p>
          </div>
          <Link to="/assessments" className="member-action-btn">Continue Journey</Link>
        </section>

        <section className="cosmic-section member-hub-card living-section todays-mission-card">
          <p className="section-kicker">Today’s Mission</p><h2>One day. One practice. One contribution.</h2>
          <ul className="mission-list">{missionItems.map((item) => <li key={item}><span>✦</span>{item}</li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card living-section recent-growth-card">
          <p className="section-kicker">Recent Growth</p><h2>Momentum is building</h2>
          <ul className="recent-growth-list">{recentGrowthItems.map((item) => <li key={item}>✓ {item}</li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section future-hook-section coming-soon-section">
          <div className="section-heading-row"><div><p className="section-kicker">Community Characteristics</p><h2>Strengths you can intentionally develop</h2></div><strong className="coming-soon-badge">Coming Soon</strong></div>
          <p>Your assessment history will soon reveal the strengths you consistently demonstrate and the characteristics you can intentionally develop.</p>
          <p className="coming-soon-note">This feature is currently being built. No characteristic scoring is active.</p>
          <div className="placeholder-card-grid">{["Cooperation", "Leadership", "Stewardship", "Initiative", "Integrity", "Communication"].map((item) => <article key={item}><span>✦</span><strong>{item}</strong><small>Coming Soon</small></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section future-hook-section archetype-section coming-soon-section">
          <div className="section-heading-row"><div><p className="section-kicker">Community Archetypes</p><h2>Future community roles and pathways</h2></div><strong className="coming-soon-badge">Coming Soon</strong></div>
          <p>Discover the community roles that best match your strengths and learn how to intentionally grow toward new roles.</p>
          <div className="placeholder-card-grid placeholder-card-grid--three">{["Builder", "Steward", "Organizer"].map((item) => <article key={item}><span>◌</span><strong>{item}</strong><small>Coming Soon</small></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section community-placeholder-card coming-soon-section">
          <div className="section-heading-row"><div><p className="section-kicker">Community Opportunities</p><h2>Personalized ways to contribute</h2></div><strong className="coming-soon-badge">Coming Soon</strong></div>
          <p>Receive personalized opportunities to contribute your talents to the community.</p>
          <div className="placeholder-card-grid">{["Upcoming Activities", "Volunteer Opportunities", "Business Opportunities", "Discussion Groups", "Study Circles"].map((item) => <article key={item}><span>✺</span><strong>{item}</strong><small>Coming Soon</small></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section continue-journey-card">
          <p className="section-kicker">Continue Your Journey</p><h2>Choose the next right action</h2>
          <div className="journey-action-grid"><Link to="/assessments/center" className="member-action-btn">Continue Latest Assessment</Link><Link to="/assessments" className="member-action-btn member-action-btn--secondary">Take Recommended Assessment</Link><Link to="/assessments" className="member-action-btn member-action-btn--secondary">Browse Assessments</Link><Link to="/assessments" className="member-action-btn member-action-btn--ghost">Assessment History</Link></div>
          {completedAssessments.length ? <ul className="star-timeline">{completedAssessments.slice(0, 3).map((item) => <li key={item.result_id || item.assessment_id || item.assessment_name}><strong>{item.assessment_name}</strong><span>{resultLabel(item)} · {item.completion_status || "completed"}</span></li>)}</ul> : <p>Your assessment history will appear here automatically after Garvey syncs results.</p>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section learning-hub-card">
          <p className="section-kicker">Learning</p><h2>Build knowledge into daily practice</h2>
          <div className="learning-hub-grid"><Link to="/library"><strong>Books</strong><span>Continue Reading</span></Link><Link to="/study"><strong>Audiobooks</strong><span>Listen and study</span></Link><a href="/languages/swahili.html"><strong>Swahili</strong><span>{swahiliWord ? `Today: ${swahiliWord.swahili}` : "Practice language"}</span></a><a href="/languages/yoruba.html"><strong>Yoruba</strong><span>Continue Learning</span></a><Link to="/brain-training"><strong>Adaptive Learning</strong><span>Train memory and focus</span></Link><Link to="/timeline"><strong>Historical Study</strong><span>{historicalSpotlightTitle}</span></Link></div>
        </section>


        <section className="cosmic-section member-hub-card member-hub-card--wide living-section star-rewards-card">
          <div className="section-heading-row"><div><p className="section-kicker">STAR Rewards</p><h2>Recognition for participation</h2></div><strong className="trust-badge">{currentStar} STAR</strong></div>
          <div className="journey-summary-grid reward-summary-grid"><article><span>Current STAR</span><strong>{currentStar}</strong><small>{currentRank}</small></article><article><span>Latest Reward</span><strong>{latestReward}</strong><small>Existing reward data</small></article><article><span>Achievements</span><strong>{growthBadges.length || starRewards.filter((reward) => reward.unlocked).length}</strong><small>Unlocked badges and rewards</small></article><article><span>Next Reward Goal</span><strong>{nextRewardGoal}</strong><small>Preserves current reward logic</small></article></div>
          <ul className="star-reward-list">{starRewards.map((reward) => <li key={reward.title} className={reward.unlocked ? "is-unlocked" : ""}><span>{reward.title}</span><strong>{reward.unlocked ? "Unlocked" : `${reward.star_needed} STAR needed`}</strong></li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide community-trust-card" aria-label="Community Trust">
          <p className="section-kicker">Existing Community Trust</p>
          <div className="community-trust-header"><div><h2>Community Trust</h2><p>Existing verification and contribution data remains available.</p></div><strong className="trust-badge">{trust.leadership_level || "Community Member"}</strong></div>
          <div className="trust-score-layout"><article className="trust-score-card"><span>Trust Score</span><strong>{trustPercent}%</strong><div className="star-progress-track"><i style={{ width: `${trustPercent}%` }} /></div></article><article><span>Verified Contributions</span><strong>{trust.verified_contributions ?? 0}</strong></article><article><span>Verifications Completed</span><strong>{trust.verifications_completed ?? 0}</strong></article><article><span>Consistency Streak</span><strong>{trust.consistency_streak ?? 0} Days</strong></article></div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section verification-requests-card">
          <p className="section-kicker">Community Verification</p><h2>Help verify community work</h2>
          {verificationRequests.length === 0 ? <p>No verification requests are open right now. When members submit proof of community work, you can help verify and earn STAR.</p> : <div className="verification-request-grid">{verificationRequests.map((request) => <article key={request.activity_id}><h3>{request.labor_category}</h3><p><strong>Submitted by:</strong> {request.submitted_by}</p><p><strong>Content/activity:</strong> {request.content || request.activity_type}</p><p><strong>Status:</strong> {request.status}</p><p><strong>Confirmations:</strong> {request.current_confirmations}/{request.required_confirmations}</p><strong className="star-reward-label">+{request.star_reward} STAR for verification</strong></article>)}</div>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section star-opportunities-card">
          <p className="section-kicker">STAR Engine</p><h2>Today’s STAR Opportunities</h2>
          <div className="star-opportunity-grid">{starOpportunities.map((item) => <a key={item.activity_type} href={item.href} className="star-opportunity"><span>{item.title}</span><strong>+{item.star} STAR</strong></a>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section community-activity-card">
          <p className="section-kicker">Recent Community Labor Activity</p><h2>Community Activity</h2>
          {recentCommunityActivity.length === 0 ? <p>Community labor activity will appear here as members learn, submit proof, and verify one another.</p> : <ul className="activity-feed">{recentCommunityActivity.map((item) => <li key={item.id}><span className="highlight">{item.message}</span><div>{item.timestamp ? new Date(item.timestamp).toLocaleDateString() : "Recently"} · {item.status} · +{item.star_award || 0} STAR</div></li>)}</ul>}
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section star-leaderboard-card">
          <p className="section-kicker">Celebration Board</p><h2>Community Leaderboards</h2>
          <div className="star-leaderboard-grid">{Object.entries(leaderboards).map(([name, rows]) => <article key={name}><h3>{name.replaceAll("_", " ")}</h3>{rows?.length ? rows.slice(0, 3).map((row, idx) => <p key={`${name}-${row.user_id}`}>#{idx + 1} Member {row.user_id}: {row.star} STAR</p>) : <p>Be the first this week.</p>}</article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section community-vision-banner">
          <p className="section-kicker">Remember Why You’re Here</p>
          <h2>Every step strengthens both you and the community.</h2>
          <p>Every lesson completed. Every assessment taken. Every STAR earned. Every book read. Every act of service.</p>
          <strong>Together we are building a thriving, self-sufficient community.</strong>
        </section>
      </main>

      {membership?.type === "community_member" && !community?.community_onboarding_completed ? <section className="cosmic-section builder-dashboard-section"><h2>🌱 Community Member First 5 Minutes</h2><p>Start with a simple path: choose interests, choose a first learning path, prepare for Discord, and complete one daily mission.</p><Link to="/community/onboarding" className="member-action-btn member-action-btn--secondary">Start Community Onboarding</Link></section> : null}

      {community?.community_onboarding_completed ? <section className="cosmic-section builder-dashboard-section"><h2>🌱 Community Onboarding</h2><div className="builder-dashboard-grid"><article><h3>First Start Completed</h3><p><strong>Learning path:</strong> {communityOnboarding.selected_learning_path || "Not selected"}</p><p><strong>First daily mission:</strong> {community?.first_daily_mission_completed ? "Completed" : "Not completed"}</p></article><article><h3>Learning Interests</h3><p>{Array.isArray(communityOnboarding.selected_interests) && communityOnboarding.selected_interests.length ? communityOnboarding.selected_interests.join(" · ") : "No interests selected yet."}</p></article></div></section> : null}

      {communityUpdates.length > 0 ? <section className="cosmic-section"><h2>📡 Command Updates</h2><ul className="activity-feed">{communityUpdates.map((update) => <li key={update}>{update}</li>)}</ul></section> : null}

      {isBuilder ? <section className="cosmic-section builder-dashboard-section"><h2>🛠️ Builder Participation</h2><div className="builder-dashboard-grid"><article><h3>Activation State</h3><p><strong>Builder level:</strong> {builder?.builder_level || "not_started"}</p><p><strong>Onboarding completed:</strong> {builder?.onboarding_completed ? "Yes" : "No"}</p><p><strong>First challenge completed:</strong> {builder?.first_challenge_completed ? "Yes" : "No"}</p><p><strong>First contribution completed:</strong> {builder?.first_contribution_completed ? "Yes" : "No"}</p>{builder?.onboarding_completed ? <p>Your activation is recorded. Use the dashboard to continue participating.</p> : <Link to="/builder/onboarding" className="member-action-btn member-action-btn--secondary">Continue Builder Activation</Link>}</article><article><h3>Selected Builder Lane</h3><p>{builderActivation.team || "Choose a Builder team during activation."}</p><p>{Array.isArray(builderActivation.interests) && builderActivation.interests.length ? builderActivation.interests.join(" · ") : "Interests are not selected yet."}</p></article><article><h3>Contribution History</h3>{contributionHistory.length === 0 ? <p>No Builder contributions have been tracked yet.</p> : <ul>{contributionHistory.map((contribution) => <li key={contribution.id || contribution.title}>{contribution.title || contribution.summary}</li>)}</ul>}</article><article><h3>Feedback Participation</h3><p>{builder?.feedback_participation?.summary || "Builder feedback tracking is being prepared."}</p></article><article><h3>Testing Opportunities</h3>{testingOpportunities.length === 0 ? <p>No builder tests are open today.</p> : <ul>{testingOpportunities.map((opportunity) => <li key={opportunity}>{opportunity}</li>)}</ul>}</article></div></section> : null}
    </div>
  );
}
