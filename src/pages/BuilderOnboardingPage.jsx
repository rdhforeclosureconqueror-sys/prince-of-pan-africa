import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, post } from "../api/api";
import "../styles/membership.css";

const INTERESTS = ["Education", "Economic cooperation", "Health & wellness", "Publishing", "Outreach", "Technology", "Leadership", "Local service"];
const TEAMS = [
  { id: "learning", name: "Learning Path Team", detail: "Review lessons, books, and study pathways." },
  { id: "community", name: "Community Welcome Team", detail: "Help new members feel oriented and connected." },
  { id: "testing", name: "Testing & Feedback Team", detail: "Test early tools and explain what needs improvement." },
  { id: "outreach", name: "Outreach Team", detail: "Help translate the mission into clear invitations." },
];

const initialForm = {
  introduction: "",
  interests: [],
  team: "",
  challenge: "",
  contribution: "",
  challengeCompleted: false,
  contributionCompleted: false,
};

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export default function BuilderOnboardingPage() {
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
        const builder = overview?.membership?.builder || {};
        if (!builder?.is_builder) {
          navigate("/membership/builder", { replace: true });
          return;
        }
        const onboarding = builder?.activation || {};
        setForm({
          introduction: onboarding.introduction || "",
          interests: Array.isArray(onboarding.interests) ? onboarding.interests : [],
          team: onboarding.team || "",
          challenge: onboarding.first_challenge || "",
          contribution: onboarding.first_contribution || "",
          challengeCompleted: Boolean(builder.first_challenge_completed),
          contributionCompleted: Boolean(builder.first_contribution_completed),
        });
        if (Number.isInteger(onboarding.current_step) && !builder.onboarding_completed) {
          setStep(Math.min(onboarding.current_step, 5));
        }
      })
      .catch((err) => setError(err.message || "Unable to load Builder activation."))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [navigate]);

  const canContinue = useMemo(() => {
    if (step === 0) return true;
    if (step === 1) return form.introduction.trim().length >= 10;
    if (step === 2) return form.interests.length > 0;
    if (step === 3) return Boolean(form.team);
    if (step === 4) return form.challenge.trim().length >= 8;
    if (step === 5) return form.contribution.trim().length >= 8;
    return true;
  }, [form, step]);

  async function saveProgress(nextStep = step, completed = false) {
    setSaving(true);
    setError("");
    try {
      await post("/member/builder/onboarding", {
        introduction: form.introduction,
        interests: form.interests,
        team: form.team,
        first_challenge: form.challenge,
        first_contribution: form.contribution,
        first_challenge_completed: form.challengeCompleted,
        first_contribution_completed: form.contributionCompleted,
        current_step: nextStep,
        steps_completed: Array.from({ length: completed ? 7 : nextStep }, (_, index) => index),
        completed,
      });
      if (completed) setStep(6);
      else setStep(nextStep);
    } catch (err) {
      setError(err.message || "Unable to save Builder activation.");
    } finally {
      setSaving(false);
    }
  }

  async function finishOnboarding() {
    await saveProgress(6, true);
  }

  if (loading) return <div className="admin-loading">Loading Builder activation...</div>;

  return (
    <main className="membership-shell builder-onboarding-shell">
      <section className="membership-hero cosmic-readable-shell">
        <p className="membership-kicker">Builder Activation</p>
        <h1>Start Building With Purpose</h1>
        <p className="membership-subtitle">This first Builder experience turns your subscription into a participation pathway: why you joined, what to do next, and how you can contribute.</p>
        <div className="builder-progress" aria-label="Builder activation progress">
          {Array.from({ length: 7 }).map((_, index) => <span key={index} className={index <= step ? "active" : ""}>{index + 1}</span>)}
        </div>
      </section>

      <section className="membership-section cosmic-readable-shell builder-step-card">
        {error && <p className="membership-error" role="alert">{error}</p>}
        {step === 0 && <><p className="membership-kicker">Welcome Flow</p><h2>You are not just buying access.</h2><p>Builder Membership means you are entering an active role. Your first mission is to clarify your reason, pick a lane, complete one community challenge, and name your first useful contribution.</p></>}
        {step === 1 && <><p className="membership-kicker">Introduce Yourself</p><h2>Why did you join?</h2><textarea value={form.introduction} onChange={(e) => setForm({ ...form, introduction: e.target.value })} placeholder="Share your name, location if you want, and what called you to help build." /></>}
        {step === 2 && <><p className="membership-kicker">Choose Interests</p><h2>What parts of the mission pull your attention?</h2><div className="builder-choice-grid">{INTERESTS.map((interest) => <button type="button" key={interest} className={form.interests.includes(interest) ? "selected" : ""} onClick={() => setForm({ ...form, interests: toggleValue(form.interests, interest) })}>{interest}</button>)}</div></>}
        {step === 3 && <><p className="membership-kicker">Choose Team</p><h2>Pick your first Builder lane.</h2><div className="builder-team-grid">{TEAMS.map((team) => <button type="button" key={team.id} className={form.team === team.id ? "selected" : ""} onClick={() => setForm({ ...form, team: team.id })}><strong>{team.name}</strong><span>{team.detail}</span></button>)}</div></>}
        {step === 4 && <><p className="membership-kicker">First Community Challenge</p><h2>Complete one visible community action.</h2><p>Choose one: support a Black-owned business, share a useful learning insight, spotlight a member, or document a local service action.</p><textarea value={form.challenge} onChange={(e) => setForm({ ...form, challenge: e.target.value })} placeholder="Describe the challenge you will complete first." /><label className="builder-confirmation"><input type="checkbox" checked={form.challengeCompleted} onChange={(e) => setForm({ ...form, challengeCompleted: e.target.checked })} /> I have actually completed this first community challenge.</label></>}
        {step === 5 && <><p className="membership-kicker">First Contribution</p><h2>Name one contribution you can make this week.</h2><p>Keep it practical. No rewards or gamification yet — just useful participation.</p><textarea value={form.contribution} onChange={(e) => setForm({ ...form, contribution: e.target.value })} placeholder="Example: I can test the library onboarding and send three notes by Friday." /><label className="builder-confirmation"><input type="checkbox" checked={form.contributionCompleted} onChange={(e) => setForm({ ...form, contributionCompleted: e.target.checked })} /> I have actually delivered this first contribution.</label></>}
        {step === 6 && <><p className="membership-kicker">Builder Recognition</p><h2>Builder activation completed.</h2><p>You are recognized as an activated Builder through participation tracking. Follow through on anything not completed yet, then return to the dashboard to keep contributing.</p><div className="builder-tracking-grid"><span>onboarding_completed: true</span><span>first_challenge_completed: {form.challengeCompleted ? "true" : "false"}</span><span>first_contribution_completed: {form.contributionCompleted ? "true" : "false"}</span><span>builder_level: activated_builder</span></div><Link to="/dashboard" className="membership-btn membership-btn--green">Go to Builder Dashboard</Link></>}

        {step < 6 && <div className="membership-cta-row"><button type="button" className="membership-btn membership-btn--ghost" disabled={step === 0 || saving} onClick={() => saveProgress(step - 1)}>Back</button>{step < 5 ? <button type="button" className="membership-btn membership-btn--green" disabled={!canContinue || saving} onClick={() => saveProgress(step + 1)}>Save and Continue</button> : <button type="button" className="membership-btn membership-btn--green" disabled={!canContinue || saving} onClick={finishOnboarding}>{saving ? "Saving…" : "Complete Activation"}</button>}</div>}
      </section>
    </main>
  );
}
