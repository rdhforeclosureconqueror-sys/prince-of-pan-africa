import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getExecutionPlans } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const list = (items, render = (x) => x, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.id || x}-${i}`}>{render(x)}</li>)}</ul> : <p>{empty}</p>;

function PlanCard({ plan }) {
  return <article className="society-card">
    <p className="society-kicker">{plan.category} · {plan.priority} priority · readiness {plan.readiness_score}</p>
    <h2>{plan.objective}</h2>
    <p>{plan.why_this_matters}</p>
    <p><strong>Confidence:</strong> {plan.confidence} · <strong>Effort:</strong> {plan.estimated_effort} · <strong>Time:</strong> {plan.time_estimate}</p>
    <p><strong>Estimated cost:</strong> {plan.estimated_cost}</p>
    <p><strong>Manual Review Required:</strong> {plan.requires_manual_review ? "Yes" : "No"} · <strong>No Execution Performed:</strong> {plan.no_execution_performed ? "Yes" : "No"}</p>
    <details><summary>Plan details</summary>
      <h3>Expected Impact</h3>{list(plan.expected_impact)}
      <h3>Required Roles</h3>{list(plan.required_roles)}
      <h3>Required Skills</h3>{list(plan.required_skills)}
      <h3>Required Members</h3>{list(plan.required_members)}
      <h3>Required Institutions</h3>{list(plan.required_institutions)}
      <h3>Required Containers</h3>{list(plan.required_containers)}
      <h3>Dependencies</h3>{list(plan.dependencies)}
      <h3>Risks</h3>{list(plan.risks)}
      <h3>Mitigation Suggestions</h3>{list(plan.mitigation_suggestions)}
      <h3>Recommended Sequence of Steps</h3>{list(plan.recommended_sequence_of_steps, (s) => <><strong>{s.sequence}.</strong> {s.step}</>)}
      <h3>Milestones</h3>{list(plan.milestones)}
      <h3>Success Metrics</h3>{list(plan.success_metrics)}
      <h3>Required Resources</h3>{list(plan.required_resources)}
      <h3>Community Benefit</h3><p>{plan.estimated_community_benefit}</p>
      <h3>Institutional Benefit</h3><p>{plan.estimated_institutional_benefit}</p>
      <h3>Evidence Supporting Recommendation</h3>{list(plan.evidence_supporting_recommendation)}
      <h3>Missing Evidence</h3>{list(plan.missing_evidence)}
      <h3>Assumptions</h3>{list(plan.assumptions)}
      <h3>Manual Review Requirements</h3>{list(plan.manual_review_requirements)}
    </details>
  </article>;
}

function Section({ title, children }) { return <section className="society-card"><h2>{title}</h2>{children}</section>; }
function PlanSection({ title, items }) { return <Section title={title}><div className="society-grid">{items?.length ? items.map((p) => <PlanCard key={p.id} plan={p} />) : <p>No plans in this section.</p>}</div></Section>; }

export default function ExecutionPlanningPage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { if (isAdmin) getExecutionPlans(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!isAdmin) return <main className="society-builder-shell"><h1>Execution Planning</h1><p className="society-warning">Admin permission is required.</p></main>;
  if (!data) return <main className="society-builder-shell"><p>Loading Execution Planning...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const d = data.dashboard || {};
  return <main className="society-builder-shell">
    <p className="society-kicker">Phase 8 · Execution Planning Layer</p>
    <h1>Execution Planning Dashboard</h1>
    <p className="society-warning">These are recommendations only. No workflows, assignments, notifications, tasks, calendar events, Kanban cards, or database writes are performed.</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Executive Summary</h2><p><strong>Total plans:</strong> {d.executive_summary?.total_plans}</p><p><strong>Top plan:</strong> {d.executive_summary?.top_plan}</p><p><strong>Readiness Score:</strong> {d.readiness_score}</p><p>{d.executive_summary?.read_only_boundary}</p></article>
      <article className="society-card"><h2>Intelligence Inputs</h2>{list(data.intelligence_inputs)}</article>
      <article className="society-card"><h2>Plan Categories</h2>{list(data.plan_categories)}</article>
    </section>
    <PlanSection title="Recommended Plans" items={d.recommended_plans} />
    <PlanSection title="Quick Wins" items={d.quick_wins} />
    <PlanSection title="Long-Term Initiatives" items={d.long_term_initiatives} />
    <Section title="Timeline View"><pre>{JSON.stringify(d.timeline_view, null, 2)}</pre></Section>
    <Section title="Dependencies">{list(d.dependencies)}</Section>
    <Section title="Required People">{list(d.required_people)}</Section>
    <Section title="Required Resources">{list(d.required_resources)}</Section>
    <Section title="Expected Outcomes">{list(d.expected_outcomes)}</Section>
    <Section title="Risks">{list(d.risks)}</Section>
    <Section title="Success Metrics">{list(d.success_metrics)}</Section>
    {data.debug ? <section className="society-card"><h2>Admin Debug</h2><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={societyId ? `/societies/${societyId}` : "/societies"}>Back to Society dashboard</Link></div>
  </main>;
}
