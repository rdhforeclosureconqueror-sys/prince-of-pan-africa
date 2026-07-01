import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addFirstTenMember,
  advanceSocietyStage,
  applyForChapter,
  getSociety,
  saveBlueprintAudit,
  saveCovenant,
  savePurpose,
  activateFirst100DaysContainer,
  getActiveContainer,
} from "../api/societyBuilder";
import "../styles/societyBuilder.css";

const DEFAULT_COVENANT = `We will show up consistently.
We will contribute as agreed.
We will keep records.
We will protect privacy.
We will handle money transparently.
We will disagree without destroying the room.
We will not use the society for personal gain without disclosure.
We will honor elders and train youth.
We will build systems that can outlive us.`;

const LABELS = {
  independent_society: "Independent Society",
  pending_review: "Pending Review",
  main_hub: "Main Hub",
  state_hub: "State Hub",
  city_hub: "City Hub",
  local_society: "Local Society",
  approved: "Approved",
  active: "Active",
  draft: "Draft",
  independent: "Independent",
  changes_requested: "Changes Requested",
  declined: "Declined",
};
const humanize = (value) => LABELS[value] || value || "Not set";
const scoreFields = [
  ["trust_score", "Trust"],
  ["relationships_score", "Relationships"],
  ["mutual_aid_score", "Mutual Aid"],
  ["organization_score", "Organization"],
  ["institutions_score", "Institutions"],
  ["businesses_score", "Businesses"],
  ["property_score", "Property"],
  ["community_wealth_score", "Community Wealth"],
  ["political_power_score", "Political Power"],
];

export default function SocietyHomePage() {
  const { societyId } = useParams();
  const [data, setData] = useState(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [first, setFirst] = useState({ name: "", role: "Member", status: "Considering", reliability_score: 3, confidentiality_score: 3, skill_capacity_score: 3, financial_steadiness_score: 3, relationship_capacity_score: 3 });
  const [purpose, setPurpose] = useState({ community_served: "", recurring_problem: "", first_focus: "", member_contribution: "show up consistently and contribute as agreed", day_100_goal: "long-term community capacity", not_doing_yet: "" });
  const [covenant, setCovenant] = useState(DEFAULT_COVENANT);
  const [audit, setAudit] = useState(Object.fromEntries(scoreFields.map(([key]) => [key, 3])));
  const [activeContainer, setActiveContainer] = useState(null);

  async function load() {
    const next = await getSociety(societyId);
    setData(next);
    try {
      const container = await getActiveContainer(societyId);
      setActiveContainer(container.container);
    } catch (_) {
      setActiveContainer(null);
    }
    return next;
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [societyId]);

  useEffect(() => {
    const s = data?.society;
    if (!s) return;
    if (s.latest_purpose) setPurpose((prev) => ({ ...prev, ...s.latest_purpose }));
    if (s.latest_covenant?.covenant_text) setCovenant(s.latest_covenant.covenant_text);
    if (s.latest_blueprint_audit) {
      setAudit(Object.fromEntries(scoreFields.map(([key]) => [key, s.latest_blueprint_audit[key] || 3])));
    }
  }, [data?.society?.id, data?.society?.latest_purpose?.id, data?.society?.latest_covenant?.id, data?.society?.latest_blueprint_audit?.id]);

  async function run(fn, successText) {
    setError("");
    setMsg("");
    try {
      const result = await fn();
      await load();
      if (result?.ok === false) {
        const missing = result.missing?.join(", ") || "requirements not met";
        setError(`${successText} blocked. Missing: ${missing}.`);
      } else {
        setMsg(successText);
      }
      return result;
    } catch (e) {
      setError(e.message || "Action failed.");
    }
  }

  const s = data?.society;
  const summary = data?.first_ten_summary || {};
  const latestAudit = s?.latest_blueprint_audit;
  const latestPurpose = s?.latest_purpose;
  const latestCovenant = s?.latest_covenant;
  const members = s?.first_ten_members || [];
  if (!data) return <main className="society-builder-shell"><p>Loading Society Home...</p>{error && <p className="society-warning">{error}</p>}</main>;

  return <main className="society-builder-shell">
    <p className="society-kicker">Society Home</p><h1>{s.name}</h1><p className="society-warning">You are building the foundation before wealth arrives.</p>
    {msg && <p className="society-success">{msg}</p>}{error && <p className="society-warning">{error}</p>}
    <section className="society-grid"><article className="society-card society-active-container-card"><p className="society-kicker">🚀 Active Container</p>{activeContainer ? <><h2>{activeContainer.title}</h2><p className="trust-lede">Build the first trustworthy container.</p><p className="society-muted">Every task strengthens one part of the society: people, systems, projects, or community impact.</p><div className="trust-progress-row"><strong>Mission Progress: {activeContainer.percent_complete}%</strong><span>Day {activeContainer.current_day} · Week {activeContainer.current_week}</span></div><div className="trust-progress-bar" aria-label={`Mission Progress ${activeContainer.percent_complete}%`}><span style={{ width: `${activeContainer.percent_complete || 0}%` }} /></div><p className="trust-next">Next Milestone: <strong>{activeContainer.active_milestone?.title || "Generate Day 100 Report"}</strong></p><div className="trust-mini-stats"><span>📅 This Week: {activeContainer.task_counts?.this_week || 0}</span><span>⏳ Blocked: {activeContainer.task_counts?.waiting || 0}</span></div><div className="society-actions"><Link className="society-btn" to={`/societies/${s.id}/trust-board`}>Open Trust Board</Link><Link className="society-btn secondary" to={`/societies/${s.id}/intelligence`}>Open Society Intelligence</Link><Link className="society-btn secondary" to={`/societies/${s.id}/opportunities`}>Open Opportunity Intelligence</Link><Link className="society-btn secondary" to={`/societies/${s.id}/decision-support`}>Open Decision Support</Link><Link className="society-btn secondary" to={`/societies/${s.id}/execution-plans`}>Open Execution Plans</Link><Link className="society-btn secondary" to={`/societies/${s.id}/trust-board`}>View How This Works</Link></div></> : <><h2>🚀 Start the First 100 Days Container</h2><p>This will turn the handbook into milestones, tasks, and weekly work for your society.</p><button className="society-btn" onClick={() => run(() => activateFirst100DaysContainer(s.id), "First 100 Days Container started.")}>Start the First 100 Days Container</button></>}</article></section>
    <section className="society-grid"><article className="society-card"><h2>Foundation status</h2><p>Stage: {humanize(s.lifecycle_stage)}</p><p>Chapter level: {humanize(s.chapter_level)}</p><p>Affiliation: {humanize(s.affiliation_status)}</p><ul className="society-progress-list"><li>Blueprint Audit: {s.blueprint_audit_completed ? "Complete" : "Needed"}</li><li>Purpose Builder: {s.purpose_completed ? "Complete" : "Needed"}</li><li>Covenant: {s.covenant_completed ? "Complete" : "Needed"}</li><li>Missing critical roles: {s.missing_critical_roles?.join(", ") || "none"}</li></ul><button className="society-btn secondary" onClick={() => run(() => applyForChapter(s.id), "Chapter application submitted.")}>Apply to Register a Chapter</button></article>
    <article className="society-card"><h2>Blueprint Audit</h2><p>Score each MVP 1 foundation area from 1 (weak) to 5 (strong).</p><div className="society-form compact">{scoreFields.map(([key, label]) => <label key={key}>{label}<select value={audit[key]} onChange={(e) => setAudit({ ...audit, [key]: Number(e.target.value) })}>{[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>)}<label>Notes<textarea value={audit.notes || ""} onChange={(e) => setAudit({ ...audit, notes: e.target.value })} /></label></div><button className="society-btn" onClick={() => run(() => saveBlueprintAudit(s.id, audit), "Blueprint Audit saved.")}>Save Blueprint Audit</button>{latestAudit && <div className="society-result"><p>Weakest area: {latestAudit.weakest_area}</p><p>Strongest area: {latestAudit.strongest_area}</p><p>Recommended next step: {latestAudit.recommended_next_step}</p>{latestAudit.warning && <p className="society-warning">{latestAudit.warning}</p>}</div>}</article></section>
    <section className="society-grid"><article className="society-card"><h2>Name Your First Ten</h2><div className="society-form compact"><label>Name<input value={first.name} onChange={(e) => setFirst({ ...first, name: e.target.value })} /></label><label>Role<select value={first.role} onChange={(e) => setFirst({ ...first, role: e.target.value })}>{["Member", "Facilitator", "Treasurer", "Assistant Treasurer", "Recordkeeper", "Care Coordinator"].map((r) => <option key={r}>{r}</option>)}</select></label></div><button className="society-btn" onClick={() => run(() => addFirstTenMember(s.id, first), "First Ten member added.")}>Add First Ten Member</button><div className="society-result"><p>Total named: {summary.total || 0}</p><p>Missing critical roles: {summary.missing_critical_roles?.join(", ") || "none"}</p>{members.length ? <ul>{members.map((m) => <li key={m.id}>{m.name} — {m.role} ({m.status})</li>)}</ul> : <p>No First Ten members named yet.</p>}</div></article>
    <article className="society-card"><h2>Purpose Builder</h2><div className="society-form compact"><label>Who does this society serve?<input value={purpose.community_served} onChange={(e) => setPurpose({ ...purpose, community_served: e.target.value })} /></label><label>Recurring problem<input value={purpose.recurring_problem} onChange={(e) => setPurpose({ ...purpose, recurring_problem: e.target.value })} /></label><label>First focus<input value={purpose.first_focus} onChange={(e) => setPurpose({ ...purpose, first_focus: e.target.value })} /></label><label>Member contribution<input value={purpose.member_contribution} onChange={(e) => setPurpose({ ...purpose, member_contribution: e.target.value })} /></label><label>Day 100 goal<input value={purpose.day_100_goal} onChange={(e) => setPurpose({ ...purpose, day_100_goal: e.target.value })} /></label><label>Not doing yet<textarea value={purpose.not_doing_yet} onChange={(e) => setPurpose({ ...purpose, not_doing_yet: e.target.value })} /></label></div><button className="society-btn" onClick={() => run(() => savePurpose(s.id, purpose), "Purpose saved.")}>Save Purpose</button>{latestPurpose?.purpose_statement && <div className="society-result"><strong>Saved purpose statement</strong><p>{latestPurpose.purpose_statement}</p>{latestPurpose.refinement_prompt && <p>{latestPurpose.refinement_prompt}</p>}</div>}</article>
    <article className="society-card"><h2>Covenant</h2><div className="society-form compact"><label>Default covenant text<textarea rows="10" value={covenant} onChange={(e) => setCovenant(e.target.value)} /></label></div><button className="society-btn" onClick={() => run(() => saveCovenant(s.id, { covenant_text: covenant, version: "v1", status: "Active", accepted_by_members: [] }), "Covenant saved.")}>Save Covenant</button>{latestCovenant && <div className="society-result"><p>Status: {humanize(latestCovenant.status)}</p><p>Version: {latestCovenant.version}</p></div>}</article>
    <article className="society-card"><h2>Stage checks</h2><button className="society-btn secondary" onClick={() => run(() => advanceSocietyStage(s.id, "Forming"), "Advanced to Forming.")}>Advance to Forming</button><button className="society-btn secondary" onClick={() => run(() => advanceSocietyStage(s.id, "Foundation Phase"), "Advanced to Foundation Phase.")}>Advance to Foundation Phase</button><p className="society-muted">If blocked, the exact missing requirements will appear above.</p></article></section>
  </main>;
}
