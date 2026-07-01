import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDecisionSupport } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const list = (items, render = (x) => x, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.id || x}-${i}`}>{render(x)}</li>)}</ul> : <p>{empty}</p>;

function DecisionCard({ decision }) {
  const scores = decision.scores || {};
  return <article className="society-card">
    <p className="society-kicker">{decision.decision_type} · {decision.priority} priority</p>
    <h2>{decision.title}</h2>
    <p>{decision.reasoning}</p>
    <p><strong>Priority:</strong> {scores.overall_priority?.score} · <strong>Impact:</strong> {decision.impact_score} · <strong>Effort:</strong> {decision.effort_score} · <strong>Urgency:</strong> {decision.urgency} · <strong>Confidence:</strong> {decision.confidence}</p>
    <p><strong>Manual Review Required:</strong> {decision.requires_manual_review ? "Yes" : "No"} · <strong>No Workflow Executed:</strong> {decision.no_workflow_executed ? "Yes" : "No"}</p>
    <details><summary>Evidence, tradeoffs, dependencies, and score explanations</summary>
      <h3>Evidence</h3>{list(decision.evidence)}
      <h3>Missing Evidence</h3>{list(decision.missing_evidence)}
      <h3>Tradeoffs</h3>{list(decision.tradeoffs)}
      <h3>Dependencies</h3>{list(decision.dependencies)}
      <h3>Expected Outcomes</h3>{list(decision.expected_outcomes)}
      <h3>Assumptions</h3>{list(decision.assumptions)}
      <h3>Score Explanations</h3>{list(Object.entries(scores), ([name, score]) => <><strong>{name}:</strong> {score.score} — {score.why}</>)}
      <h3>Related Entities</h3><pre>{JSON.stringify(decision.related_entities || {}, null, 2)}</pre>
    </details>
  </article>;
}

function Section({ title, items }) {
  return <section className="society-card"><h2>{title}</h2><div className="society-grid">{items?.length ? items.map((d) => <DecisionCard key={d.id} decision={d} />) : <p>No recommendations in this area.</p>}</div></section>;
}

export default function DecisionSupportPage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { if (isAdmin) getDecisionSupport(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!isAdmin) return <main className="society-builder-shell"><h1>Decision Support</h1><p className="society-warning">Admin permission is required.</p></main>;
  if (!data) return <main className="society-builder-shell"><p>Loading Decision Support...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const d = data.dashboard || {};
  return <main className="society-builder-shell">
    <p className="society-kicker">Phase 7 · Decision Support Layer</p>
    <h1>Executive Decision Support System</h1>
    <p>This page is 100% read-only. It never automates decisions, executes workflows, assigns members, creates tasks, sends notifications, creates calendar events, or creates Kanban cards. Human leaders make every final decision.</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Executive Summary</h2><p><strong>Total recommendations:</strong> {d.executive_summary?.total_recommendations}</p><p><strong>Top priority:</strong> {d.executive_summary?.top_priority}</p><p>{d.executive_summary?.read_only_boundary}</p></article>
      <article className="society-card"><h2>Intelligence Inputs</h2>{list(data.intelligence_inputs)}</article>
      <article className="society-card"><h2>Warnings</h2>{list(data.warnings)}</article>
    </section>
    <Section title="Top 10 Priorities" items={d.top_10_priorities} />
    <Section title="Quick Wins" items={d.quick_wins} />
    <Section title="High Impact / Low Effort" items={d.high_impact_low_effort} />
    <Section title="High Impact / High Effort" items={d.high_impact_high_effort} />
    <Section title="Critical Risks" items={d.critical_risks} />
    <Section title="Leadership Decisions" items={d.leadership_decisions} />
    <Section title="Institution Decisions" items={d.institution_decisions} />
    <Section title="Container Decisions" items={d.container_decisions} />
    <Section title="Business Decisions" items={d.business_decisions} />
    <Section title="Resource Allocation" items={d.resource_allocation} />
    <Section title="Strategic Roadmap" items={d.strategic_roadmap} />
    {data.debug ? <section className="society-card"><h2>Admin Debug</h2><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={societyId ? `/societies/${societyId}` : "/societies"}>Back to Society dashboard</Link></div>
  </main>;
}
