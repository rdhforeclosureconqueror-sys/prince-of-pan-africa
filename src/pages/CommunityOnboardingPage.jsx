import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, post } from "../api/api";
import "../styles/membership.css";

const INTERESTS = ["African history", "Swahili language", "Economic cooperation", "Health & wellness", "Leadership", "Publishing & storytelling", "Family legacy", "Local service"];

const LEARNING_PATHS = [
  { id: "foundations", name: "Foundational Texts", detail: "Start with the core books and ideas behind the Simba wa Ujamaa mission." },
  { id: "history", name: "African History Spotlight", detail: "Use daily history study to connect memory, responsibility, and action." },
  { id: "language", name: "Swahili Foundations", detail: "Practice one word and one phrase as a daily cultural continuity habit." },
  { id: "economics", name: "Community Economics", detail: "Learn how support, ownership, trade, and cooperation strengthen community capacity." },
];

const initialForm = {
  interests: [],
  learningPath: "",
  discordPrepared: false,
  firstDailyMissionCompleted: false,
};

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export default function CommunityOnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    api("/member/overview", { method: "GET" })
      .then((overview) => {
        if (!mounted) return;
        const membershipType = overview?.membership?.type;
        if (!["community_member", "builder_member"].includes(membershipType)) {
          navigate("/membership/community", { replace: true });
          return;
        }
        const community = overview?.membership?.community || {};
        const onboarding = community?.onboarding || {};
        setForm({
          interests: Array.isArray(onboarding.selected_interests) ? onboarding.selected_interests : [],
          learningPath: onboarding.selected_learning_path || "",
          discordPrepared: Boolean(onboarding.discord_prepared),
          firstDailyMissionCompleted: Boolean(community.first_daily_mission_completed),
        });
        if (Number.isInteger(onboarding.current_step) && !community.community_onboarding_completed) {
          setStep(Math.min(onboarding.current_step, 4));
        } else if (community.community_onboarding_completed) {
          setStep(5);
        }
      })
      .catch((err) => setError(err.message || "Unable to load Community onboarding."))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [navigate]);

  const canContinue = useMemo(() => {
    if (step === 0) return true;
    if (step === 1) return form.interests.length > 0;
    if (step === 2) return Boolean(form.learningPath);
    if (step === 3) return form.discordPrepared;
    if (step === 4) return form.firstDailyMissionCompleted;
    return true;
  }, [form, step]);

  async function saveProgress(nextStep = step, completed = false) {
    setSaving(true);
    setError("");
    try {
      await post("/member/community/onboarding", {
        selected_interests: form.interests,
        selected_learning_path: form.learningPath,
        discord_prepared: form.discordPrepared,
        first_daily_mission_completed: form.firstDailyMissionCompleted,
        current_step: nextStep,
        completed,
      });
      setStep(completed ? 5 : nextStep);
    } catch (err) {
      setError(err.message || "Unable to save Community onboarding.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="admin-loading">Loading Community onboarding...</div>;

  return (
    <main className="membership-shell builder-onboarding-shell">
      <section className="membership-hero cosmic-readable-shell">
        <p className="membership-kicker">Community Member Onboarding</p>
        <h1>Your First 5 Minutes</h1>
        <p className="membership-subtitle">A simple start for Community Members: choose what you want to learn, pick one first path, prepare for Discord, and complete one daily mission.</p>
        <div className="builder-progress" aria-label="Community onboarding progress">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} className={index <= step ? "active" : ""}>{index + 1}</span>)}
        </div>
      </section>

      <section className="membership-section cosmic-readable-shell builder-step-card">
        {error && <p className="membership-error" role="alert">{error}</p>}
        {step === 0 && <><p className="membership-kicker">Welcome</p><h2>Welcome to the mission.</h2><p>Community Membership starts with a clear first action, not a complicated program. In the next few minutes, choose your learning interests, pick one path, prepare for Discord, and complete your first daily mission.</p></>}
        {step === 1 && <><p className="membership-kicker">Choose Learning Interests</p><h2>What do you want to learn first?</h2><div className="builder-choice-grid">{INTERESTS.map((interest) => <button type="button" key={interest} className={form.interests.includes(interest) ? "selected" : ""} onClick={() => setForm({ ...form, interests: toggleValue(form.interests, interest) })}>{interest}</button>)}</div></>}
        {step === 2 && <><p className="membership-kicker">Choose First Learning Path</p><h2>Pick one path to begin today.</h2><div className="builder-team-grid">{LEARNING_PATHS.map((path) => <button type="button" key={path.id} className={form.learningPath === path.id ? "selected" : ""} onClick={() => setForm({ ...form, learningPath: path.id })}><strong>{path.name}</strong><span>{path.detail}</span></button>)}</div></>}
        {step === 3 && <><p className="membership-kicker">Join / Prepare Discord</p><h2>Get ready for the community space.</h2><p>Discord integration is still being prepared. For now, make sure your Discord account is ready and save the email you joined with so your future community access can be matched.</p><label className="builder-confirmation"><input type="checkbox" checked={form.discordPrepared} onChange={(e) => setForm({ ...form, discordPrepared: e.target.checked })} /> I am ready to join the Community Member Discord space when invited.</label></>}
        {step === 4 && <><p className="membership-kicker">First Daily Mission</p><h2>Complete one small mission now.</h2><p>Choose one: read today’s historical spotlight, practice one Swahili word, open your selected learning path, or write one sentence about why you joined.</p><label className="builder-confirmation"><input type="checkbox" checked={form.firstDailyMissionCompleted} onChange={(e) => setForm({ ...form, firstDailyMissionCompleted: e.target.checked })} /> I completed my first daily mission.</label></>}
        {step === 5 && <><p className="membership-kicker">Community Onboarding Complete</p><h2>You are ready for your first week.</h2><p>Your first 5-minute start is recorded. Keep using the dashboard for daily learning and community preparation.</p><div className="builder-tracking-grid"><span>community_onboarding_completed: true</span><span>selected_interests: {form.interests.join(", ") || "none"}</span><span>selected_learning_path: {form.learningPath || "none"}</span><span>first_daily_mission_completed: {form.firstDailyMissionCompleted ? "true" : "false"}</span></div><Link to="/dashboard" className="membership-btn membership-btn--green">Go to Member Dashboard</Link></>}

        {step < 5 && <div className="membership-cta-row"><button type="button" className="membership-btn membership-btn--ghost" disabled={step === 0 || saving} onClick={() => saveProgress(step - 1)}>Back</button>{step < 4 ? <button type="button" className="membership-btn membership-btn--green" disabled={!canContinue || saving} onClick={() => saveProgress(step + 1)}>Save and Continue</button> : <button type="button" className="membership-btn membership-btn--green" disabled={!canContinue || saving} onClick={() => saveProgress(5, true)}>{saving ? "Saving…" : "Complete Onboarding"}</button>}</div>}
      </section>
    </main>
  );
}
