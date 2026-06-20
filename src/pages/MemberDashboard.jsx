import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { getAssessmentResults, getGrowthProfile } from "../api/assessments";
import { getCommunityTrustExperience, getOpenVerificationRequests, getRecentCommunityActivity, getCommunityActivityFeed, getStarExperience } from "../api/participation";
import { firstSevenDaysPathway, memberOnboardingSettings } from "../onboarding/memberOnboardingConfig";
import { completeMemberOnboardingStep, getMemberOnboardingState, mergeDetectedOnboardingSteps, saveMemberOnboardingState, startMemberOnboarding } from "../onboarding/memberOnboardingStorage";
import { getDailyHistoricalSpotlight } from "../data/dailyHistoricalSpotlights";
import ApplicationCard from "../components/ApplicationCard";
import { SIMBA_APPLICATIONS } from "../data/applications";
import { TIMELINE_A_AFRICA_ORIGINS } from "../data/timelineA_africaOrigins";
import swahiliLessons from "../../public/languages/swahili_30days.json";
import "../styles/dashboard.css";
import "../styles/applications.css";

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
  const [communityFeed, setCommunityFeed] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [growthProfile, setGrowthProfile] = useState(null);
  const [assessmentResults, setAssessmentResults] = useState([]);
  const [latestAssessmentResults, setLatestAssessmentResults] = useState([]);
  const [onboardingState, setOnboardingState] = useState(null);

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
        const [overviewRes, activityRes, starRes, trustRes, verificationRes, communityActivityRes, communityFeedRes, growthRes, assessmentResultsRes] = await Promise.all([
          api("/member/overview", { method: "GET" }),
          api("/member/activity", { method: "GET" }),
          getStarExperience(),
          getCommunityTrustExperience(),
          getOpenVerificationRequests(),
          getRecentCommunityActivity(),
          getCommunityActivityFeed(),
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
        setCommunityFeed(communityFeedRes || null);
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
  const memberId = overview?.user?.id || overview?.profile?.id || overview?.user?.email || overview?.email || memberName;
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


  const journeyPhases = ["Beginning", "Growing", "Contributing", "Leading", "Mentoring"];
  const journeyIndex = Math.min(journeyPhases.length - 1, Math.max(0, completedAssessments.length + (currentStar > 0 ? 1 : 0) + (activityCount > 3 ? 1 : 0)));
  const journeyProgress = Math.round(((journeyIndex + 1) / journeyPhases.length) * 100);
  const communityStage = isBuilder ? "Builder" : currentRank || membership?.label || "Member";
  const primaryMission = completedAssessments.length ? `Continue ${recommendedAssessment}.` : "Complete your Leadership Assessment.";
  const briefingMissions = [
    primaryMission,
    learningPath ? `Continue reading ${learningPath.title}.` : "Continue reading in the Simba library.",
    `Earn ${starOpportunities[0]?.star || 25} STAR points.`,
  ];
  const snapshotStats = [
    ["Books Read", summary?.books_completed ?? 0],
    ["Assessments Completed", growthSummary.completed_assessments ?? completedAssessments.length],
    ["STAR Earned", currentStar],
    ["Current Membership", membership?.label || membershipStatusLabel],
    ["Badges Earned", growthBadges.length || starRewards.filter((reward) => reward.unlocked).length],
    ["Learning Streak", `${currentStreak} day${currentStreak === 1 ? "" : "s"}`],
  ];
  const unfinishedActivity = recentActivity.find((item) => !["completed", "complete", "approved"].includes(String(item.status || item.completion_status || "").toLowerCase()));
  const resumeJourney = unfinishedActivity
    ? { label: unfinishedActivity.title || unfinishedActivity.activity_type?.replaceAll("_", " ") || "Continue Learning", detail: unfinishedActivity.status || "In progress", to: unfinishedActivity.href || "/dashboard" }
    : completedAssessments.length
      ? { label: `Continue ${recommendedAssessment}`, detail: currentGrowthFocus, to: "/assessments" }
      : { label: "Continue Assessment", detail: "Begin with the official Garvey assessment path.", to: "/assessments/center" };
  const achievementGallery = [
    ...growthBadges.map((badge) => ({ title: badge.label || badge.title || "Achievement", detail: badge.description || "Earned through your existing growth path.", earned: true })),
    ...starRewards.filter((reward) => reward.unlocked).map((reward) => ({ title: reward.title, detail: `${reward.star_needed || currentStar} STAR milestone`, earned: true })),
    ...(completedAssessments.length ? [{ title: "First Assessment", detail: latestAssessmentName, earned: true }] : []),
    ...(currentStar > 0 ? [{ title: "STAR Collector", detail: `${currentStar} STAR earned`, earned: true }] : []),
    { title: isBuilder ? "Community Builder" : "Community Member", detail: membership?.label || membershipStatusLabel, earned: Boolean(membership?.type || membership?.status) },
  ].filter((item, index, arr) => arr.findIndex((match) => match.title === item.title) === index).slice(0, 8);
  const weeklyWins = [
    ...completedAssessments.slice(0, 2).map((item) => `Completed ${item.assessment_name || item.title || "Garvey Assessment"}`),
    currentStar ? `Earned ${currentStar} STAR` : null,
    summary?.books_completed ? `Read ${summary.books_completed} book${summary.books_completed === 1 ? "" : "s"}` : null,
    summary?.lessons_completed ? `Completed ${summary.lessons_completed} lesson${summary.lessons_completed === 1 ? "" : "s"}` : null,
  ].filter(Boolean).slice(0, 4);


  const detectedOnboardingSteps = [
    "mission",
    completedAssessments.length ? "assessment" : null,
    currentStar > 0 ? "starAction" : null,
    (summary?.books_completed || summary?.books_previewed || summary?.audiobooks_started) ? "library" : null,
    (summary?.lessons_completed || summary?.language_lessons_completed) ? "language" : null,
    starHistory.some((item) => String(item?.activity_type || "").includes("brain_game")) ? "brainTraining" : null,
  ].filter(Boolean);
  const baseOnboardingState = onboardingState || getMemberOnboardingState(memberId);
  const activeOnboardingState = mergeDetectedOnboardingSteps(baseOnboardingState, detectedOnboardingSteps);
  const completedOnboardingSteps = new Set(activeOnboardingState.completed_steps || []);
  const onboardingComplete = Boolean(activeOnboardingState.onboarding_completed_at);
  const currentOnboardingStep = firstSevenDaysPathway.find((step) => step.key === activeOnboardingState.current_step) || firstSevenDaysPathway.find((step) => !completedOnboardingSteps.has(step.key)) || firstSevenDaysPathway[0];
  const onboardingProgress = firstSevenDaysPathway.length ? Math.round((completedOnboardingSteps.size / firstSevenDaysPathway.length) * 100) : 100;
  const showFirstTimeWelcome = !activeOnboardingState.onboarding_started_at && !onboardingComplete;
  const discordInviteUrl = memberOnboardingSettings.discordInviteUrl;

  const persistOnboarding = (nextState) => {
    const saved = saveMemberOnboardingState(memberId, nextState);
    setOnboardingState(saved);
  };
  const startOnboarding = () => persistOnboarding(startMemberOnboarding(activeOnboardingState));
  const markOnboardingStepComplete = (stepKey) => persistOnboarding(completeMemberOnboardingStep(activeOnboardingState, stepKey));

  const heartbeatFeed = communityFeed?.feed?.length ? communityFeed.feed : recentCommunityActivity;
  const announcements = communityFeed?.announcements || [];
  const dailyCommunityChallenge = communityFeed?.today_challenge || { title: "Learn one Swahili word", action: swahiliWord ? `Practice ${swahiliWord.swahili} and use it in one sentence.` : "Practice one language word and share it in your notes.", href: "/languages" };
  const weeklyCommunityGoal = communityFeed?.weekly_goal || { title: "Earn 5,000 STAR together", current: currentStar, target: 5000, percent: Math.min(100, Math.round((currentStar / 5000) * 100)) };
  const communityMilestones = communityFeed?.milestones || [
    { title: "100 Members", current: summary?.members_participating ?? 0, target: 100, percent: Math.min(100, Math.round(((summary?.members_participating ?? 0) / 100) * 100)) },
    { title: "500 Books Read", current: summary?.books_completed ?? 0, target: 500, percent: Math.min(100, Math.round(((summary?.books_completed ?? 0) / 500) * 100)) },
    { title: "10,000 STAR Earned", current: currentStar, target: 10000, percent: Math.min(100, Math.round((currentStar / 10000) * 100)) },
  ];
  const weeklySpotlight = communityFeed?.spotlight || { type: "Language Spotlight", title: swahiliWord ? swahiliWord.swahili : "Swahili Foundations", body: "Practice one word today and build cultural continuity without rushing.", href: "/languages/swahili.html" };
  const energyMeter = communityFeed?.energy_meter || { label: heartbeatFeed.length > 8 ? "Active" : heartbeatFeed.length > 2 ? "Growing" : "Quiet", basis: "Based only on visible recorded activity." };
  const futureSections = ["Local Meetups", "Study Circles", "Business Collaborations", "Investment Circles", "Mentorship", "Cooperative Purchasing", "Mutual Aid", "Community Funding"];
  const operationsApplications = SIMBA_APPLICATIONS.filter((application) => application.category === "Community Operations");
  const recentlyUsedApplications = SIMBA_APPLICATIONS.filter((application) => ["member-home", "community", "library"].includes(application.id));
  const recommendedApplications = SIMBA_APPLICATIONS.filter((application) => ["assessments", "languages", "star-rewards"].includes(application.id));

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
      <header className="mission-control member-hero dashboard-header living-hero member-home-briefing">
        <div className="briefing-copy">
          <p className="member-kicker">Member Home · Daily Briefing</p>
          <h1>{greeting}, {memberName}.</h1>
          <p className="subtitle">Welcome back. Simba is here to help you know where you are, what you accomplished, and the next step that matters.</p>
        </div>
        <div className="briefing-panel" aria-label="Today's member briefing">
          <article><span>Community Stage</span><strong>{communityStage}</strong><small>{membership?.label || "Member"}</small></article>
          <article><span>Current Journey</span><strong>{currentFocusTitle}</strong><small>{currentStage}</small></article>
          <article className="briefing-mission"><span>Today's Mission</span><ul>{briefingMissions.map((item) => <li key={item}>{item}</li>)}</ul><small>Small steps become community strength when you return with intention.</small></article>
        </div>
      </header>

      <main className="member-hub-grid living-dashboard-grid command-grid member-home-grid">

        {showFirstTimeWelcome ? (
          <section className="cosmic-section member-hub-card member-hub-card--wide living-section onboarding-welcome-card">
            <p className="section-kicker">First-Time Member Welcome</p>
            <h2>Welcome to Simba wa Ujamaa.</h2>
            <p>You are entering a Pan-African learning community built around books, language, history, assessments, STAR participation, and cooperative growth.</p>
            <div className="onboarding-action-row">
              <button type="button" className="member-action-btn" onClick={startOnboarding}>Start My First 7 Days</button>
              <button type="button" className="member-action-btn member-action-btn--secondary" onClick={() => markOnboardingStepComplete("mission")}>Explore Member Home</button>
            </div>
          </section>
        ) : null}

        {!onboardingComplete && !showFirstTimeWelcome ? (
          <section className="cosmic-section member-hub-card member-hub-card--wide living-section onboarding-progress-card">
            <div className="section-heading-row"><div><p className="section-kicker">First 7 Days</p><h2>{currentOnboardingStep ? `Day ${currentOnboardingStep.day} — ${currentOnboardingStep.title}` : "Onboarding Complete"}</h2></div><strong className="trust-badge">{onboardingProgress}% Complete</strong></div>
            <div className="onboarding-progress-bar" aria-label={`Onboarding is ${onboardingProgress}% complete`}><span style={{ width: `${onboardingProgress}%` }} /></div>
            <p>{currentOnboardingStep?.nextAction || "Choose your next Simba journey."}</p>
            {currentOnboardingStep?.key === "mission" ? <p className="onboarding-mission-copy">Simba wa Ujamaa exists to strengthen people and community through disciplined learning, cooperative economics, cultural memory, language, and daily participation.</p> : null}
            {currentOnboardingStep?.key === "discord" || currentOnboardingStep?.key === "mission" ? <div className="discord-onboarding-box"><strong>Join the Simba Discord Community</strong><p>Introduce yourself, rep your state or region, join daily discussions, and prepare for community verification later.</p>{discordInviteUrl ? <a className="member-action-btn member-action-btn--secondary" href={discordInviteUrl} target="_blank" rel="noreferrer">Open Discord Invite</a> : <small>Admin note: add VITE_SIMBA_DISCORD_INVITE_URL or VITE_DISCORD_INVITE_URL to show the live invite.</small>}</div> : null}
            <div className="onboarding-action-row">
              {currentOnboardingStep?.href ? <Link to={currentOnboardingStep.href} className="member-action-btn">Continue</Link> : null}
              {currentOnboardingStep ? <button type="button" className="member-action-btn member-action-btn--secondary" onClick={() => markOnboardingStepComplete(currentOnboardingStep.key)}>Mark Step Complete</button> : null}
            </div>
            <ol className="onboarding-checklist">{firstSevenDaysPathway.map((step) => <li key={step.key} className={completedOnboardingSteps.has(step.key) ? "is-complete" : step.key === currentOnboardingStep?.key ? "is-current" : ""}><button type="button" onClick={() => markOnboardingStepComplete(step.key)} aria-label={`Mark ${step.title} complete`}>{completedOnboardingSteps.has(step.key) ? "✓" : step.day}</button><div><strong>Day {step.day} — {step.title}</strong><span>{step.tasks.join(" · ")}</span></div></li>)}</ol>
          </section>
        ) : null}
        <section className="cosmic-section member-hub-card living-section resume-journey-card member-home-priority">
          <p className="section-kicker">Continue Where You Left Off</p>
          <h2>Resume Journey</h2>
          <p>{resumeJourney.detail}</p>
          <Link to={resumeJourney.to} className="member-action-btn">{resumeJourney.label}</Link>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section application-launcher-card member-home-priority">
          <div className="section-heading-row"><div><p className="section-kicker">Application Launcher</p><h2>Open your Community Operating System</h2></div><Link to="/applications" className="member-action-btn member-action-btn--secondary">View All Applications</Link></div>
          <p className="heartbeat-intro">Simba organizes your tools as applications: growth, learning, culture, community coordination, and connected external platforms.</p>
          <div className="dashboard-application-grid">{recentlyUsedApplications.map((application) => <ApplicationCard key={application.id} application={application} compact />)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section continue-journey-apps-card">
          <div className="section-heading-row"><div><p className="section-kicker">Recommended Applications</p><h2>Continue Your Journey</h2></div><span className="trust-badge">Favorites & pinned apps coming soon</span></div>
          <div className="dashboard-application-grid">{recommendedApplications.map((application) => <ApplicationCard key={application.id} application={application} compact />)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section application-launcher-card member-home-priority">
          <div className="section-heading-row"><div><p className="section-kicker">Community Operations</p><h2>Practice Unity Through Action</h2></div><Link to="/community/preparedness" className="member-action-btn member-action-btn--secondary">Continue Preparedness</Link></div>
          <p className="heartbeat-intro">Preparedness is the first live operations module. Future modules will coordinate projects, mutual aid, food, chapters, care, funding, and response without duplicating the architecture.</p>
          <div className="dashboard-application-grid">{operationsApplications.slice(0, 3).map((application) => <ApplicationCard key={application.id} application={application} compact />)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section community-heartbeat-card member-home-priority" id="community-feed">
          <div className="section-heading-row"><div><p className="section-kicker">Community Activity Feed</p><h2>The Heartbeat of Simba</h2></div><strong className={`energy-meter energy-meter--${String(energyMeter.label).toLowerCase()}`}>{energyMeter.label}</strong></div>
          <p className="heartbeat-intro">A cooperative feed for learning, contribution, service, and progress — not another social media timeline.</p>
          {announcements.length ? <div className="announcement-stack">{announcements.map((item) => <article key={item.id || item.title} className="activity-card activity-card--announcement"><span>{item.category || "Announcement"}</span><strong>{item.title}</strong><p>{item.body}</p></article>)}</div> : null}
          <div className="heartbeat-focus-grid">
            <article className="activity-card activity-card--challenge"><span>Today’s Challenge</span><strong>{dailyCommunityChallenge.title}</strong><p>{dailyCommunityChallenge.action}</p>{dailyCommunityChallenge.href ? <Link to={dailyCommunityChallenge.href} className="text-link">Begin mission</Link> : null}</article>
            <article className="activity-card activity-card--goal"><span>Weekly Community Goal</span><strong>{weeklyCommunityGoal.title}</strong><div className="community-progress"><span style={{ width: `${weeklyCommunityGoal.percent || 0}%` }} /></div><small>{weeklyCommunityGoal.current || 0} / {weeklyCommunityGoal.target || 0}</small></article>
            <article className="activity-card activity-card--spotlight"><span>{weeklySpotlight.type}</span><strong>{weeklySpotlight.title}</strong><p>{weeklySpotlight.body}</p>{weeklySpotlight.href ? <Link to={weeklySpotlight.href} className="text-link">Explore</Link> : null}</article>
          </div>
          <div className="activity-scroll" aria-label="Recent cooperative activity">{heartbeatFeed.length ? heartbeatFeed.map((item) => <article key={item.id || item.message} className="activity-card activity-card--feed"><span>{item.activity_type?.replaceAll("_", " ") || "Community"}</span><strong>{item.message}</strong>{item.star_award ? <small>+{item.star_award} STAR</small> : null}</article>) : <article className="activity-card activity-card--feed"><strong>A new member joined.</strong><p>Community activity will appear here as members learn, serve, and contribute.</p></article>}</div>
          <div className="milestone-grid">{communityMilestones.map((item) => <article key={item.title} className="milestone-card"><strong>{item.title}</strong><div className="community-progress"><span style={{ width: `${item.percent || 0}%` }} /></div><small>{item.current || 0} / {item.target || 0}</small></article>)}</div>
          <p className="energy-note">{energyMeter.basis}</p>
        </section>

        <section className="cosmic-section member-hub-card living-section achievement-spotlight-card member-home-priority">
          <p className="section-kicker">Recent Achievement</p>
          <h2>{recentAchievement}</h2>
          <p>{completedAssessments.length ? "Your growth work is being recognized and reflected back to you." : "Complete your first assessment to begin your achievement story."}</p>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section journey-ring-card">
          <div className="section-heading-row"><div><p className="section-kicker">Living Progress Ring</p><h2>How am I growing?</h2></div><strong className="trust-badge">{journeyPhases[journeyIndex]}</strong></div>
          <div className="journey-ring-layout">
            <div className="journey-ring" style={{ "--journey-progress": `${journeyProgress * 3.6}deg` }}><span>{journeyProgress}%</span><small>Journey</small></div>
            <ol className="journey-phase-list">{journeyPhases.map((phase, index) => <li key={phase} className={index <= journeyIndex ? "is-active" : ""}><span>{index + 1}</span><strong>{phase}</strong></li>)}</ol>
          </div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section community-snapshot-card">
          <p className="section-kicker">Community Snapshot</p><h2>What you have already built</h2>
          <div className="snapshot-grid">{snapshotStats.map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section achievement-gallery-card">
          <p className="section-kicker">Achievement Gallery</p><h2>Trophies from your path</h2>
          <div className="achievement-gallery">{achievementGallery.map((item) => <article key={item.title} className={item.earned ? "is-earned" : ""}><span>🏆</span><strong>{item.title}</strong><small>{item.detail}</small></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card living-section weekly-reflection-card">
          <p className="section-kicker">This Week</p><h2>You completed</h2>
          {weeklyWins.length ? <ul className="recent-growth-list">{weeklyWins.map((item) => <li key={item}>✓ {item}</li>)}</ul> : <p>Your weekly wins will appear as you complete assessments, earn STAR, and learn.</p>}
          <blockquote>“What is one strength you demonstrated this week?”</blockquote>
        </section>

        <section className="cosmic-section member-hub-card living-section todays-mission-card">
          <p className="section-kicker">Why it matters</p><h2>One day. One practice. One contribution.</h2>
          <ul className="mission-list">{missionItems.slice(0, 3).map((item) => <li key={item}><span>✦</span>{item}</li>)}</ul>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section upcoming-journey-card coming-soon-section">
          <div className="section-heading-row"><div><p className="section-kicker">Upcoming Journey</p><h2>Coming Soon</h2></div><strong className="coming-soon-badge">Expanding Pathways</strong></div>
          <p>These pathways are presented as an exciting preview only. No new characteristic scoring or archetype assignment is active here.</p>
          <div className="placeholder-card-grid">{futureSections.map((item) => <article key={item}><span>✺</span><strong>{item}</strong><small>Coming Soon</small></article>)}</div>
        </section>

        <section className="cosmic-section member-hub-card member-hub-card--wide living-section learning-hub-card">
          <p className="section-kicker">Learning Paths</p><h2>Quiet options when you are ready for more</h2>
          <div className="learning-hub-grid"><Link to="/library"><strong>Continue Reading</strong><span>{learningPath?.title || "Library"}</span></Link><Link to="/study"><strong>Continue Audiobook</strong><span>Listen and study</span></Link><a href="/languages/swahili.html"><strong>Continue Swahili</strong><span>{swahiliWord ? `Today: ${swahiliWord.swahili}` : "Practice language"}</span></a><a href="/languages/yoruba.html"><strong>Continue Learning</strong><span>Yoruba practice</span></a><Link to="/assessments"><strong>Continue Assessment</strong><span>{recommendedAssessment}</span></Link><Link to="/timeline"><strong>Historical Study</strong><span>{historicalSpotlightTitle}</span></Link></div>
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
