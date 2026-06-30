import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getOpportunityIntelligence } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const list = (items, render = (x) => x, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.id || x.opportunity_id || x}-${i}`}>{render(x)}</li>)}</ul> : <p>{empty}</p>;
const typeTitle = (type) => `${type.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())} Opportunities`;

function OpportunityCard({ opportunity }) {
  return <article className="society-card">
    <p className="society-kicker">{opportunity.type} · {opportunity.priority} priority</p>
    <h2>{opportunity.title}</h2>
    <p>{opportunity.reason}</p>
    <p><strong>Recommended action:</strong> {opportunity.recommended_action}</p>
    <p><strong>Confidence:</strong> {opportunity.confidence} · <strong>Evidence:</strong> {opportunity.evidence?.length || 0} · <strong>Missing:</strong> {opportunity.missing_evidence?.length || 0}</p>
    <p className="society-muted">Priority calculation: {opportunity.priority_calculation}</p>
    <details><summary>Opportunity details</summary>
      <p><strong>Manual review required:</strong> {opportunity.requires_manual_review ? "Yes" : "No"}</p>
      <p><strong>No workflow executed:</strong> {opportunity.no_workflow_executed ? "Yes" : "No"}</p>
      <p><strong>Related members:</strong> {(opportunity.related_members || []).join(", ") || "None"}</p>
      <p><strong>Related roles:</strong> {(opportunity.related_roles || []).join(", ") || "None"}</p>
      <p><strong>Related containers:</strong> {(opportunity.related_containers || []).join(", ") || "None"}</p>
      <p><strong>Related societies:</strong> {(opportunity.related_societies || []).join(", ") || "None"}</p>
      <p><strong>Related institutions:</strong> {(opportunity.related_institutions || []).join(", ") || "None"}</p>
      <h3>Evidence used</h3>{list(opportunity.evidence)}
      <h3>Missing evidence</h3>{list(opportunity.missing_evidence)}
    </details>
  </article>;
}

export default function OpportunityIntelligencePage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getOpportunityIntelligence(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!isAdmin) return <main className="society-builder-shell"><h1>Opportunity Intelligence</h1><p className="society-warning">Admin debug permission is required.</p></main>;
  if (!data) return <main className="society-builder-shell"><p>Loading Opportunity Intelligence...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const d = data.dashboard || {};
  const byType = d.by_type || {};
  const orderedTypes = ["leadership", "volunteer", "business", "institution", "education", "trust", "recognition", "role", "assessment", "mentorship", "society_growth"];
  return <main className="society-builder-shell">
    <p className="society-kicker">Opportunity Intelligence</p>
    <h1>Highest-value opportunities right now</h1>
    <p>This is a read-only decision-support layer. It does not create tasks, appointments, assignments, notifications, schedules, or workflows.</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Health Summary</h2><p><strong>{data.overall_priority?.label}</strong> priority · score {data.overall_priority?.score}</p><p>{data.overall_priority?.why}</p><p>Societies reviewed: {d.health_summary?.societies_reviewed} · Opportunities: {d.health_summary?.opportunity_count}</p></article>
      <article className="society-card"><h2>Confidence</h2><p>{data.confidence}</p><p>Evidence Count: {d.evidence_count}</p><p>Missing Evidence: {data.missing_evidence?.length || 0}</p></article>
      <article className="society-card"><h2>Recommendations</h2>{list(data.recommendations, (r) => <><strong>{r.action}</strong>: {r.why}</>)}</article>
      <article className="society-card"><h2>Warnings</h2>{list(data.warnings)}</article>
    </section>
    <section className="society-card"><h2>Top Opportunities</h2><div className="society-grid">{(d.top_opportunities || []).map((o) => <OpportunityCard key={o.id} opportunity={o} />)}</div></section>
    {[["High Priority", d.high_priority], ["Medium Priority", d.medium_priority], ["Low Priority", d.low_priority], ["Recently Changed", d.recently_changed]].map(([title, items]) => <section className="society-card" key={title}><h2>{title}</h2>{list(items, (o) => <><strong>{o.title}</strong> — {o.type} · {o.confidence}</>)}</section>)}
    {orderedTypes.map((type) => byType[type]?.length ? <section className="society-card" key={type}><h2>{typeTitle(type)}</h2><div className="society-grid">{byType[type].map((o) => <OpportunityCard key={o.id} opportunity={o} />)}</div></section> : null)}
    <section className="society-card"><h2>Missing Evidence</h2>{list(data.missing_evidence)}</section>
    {data.debug ? <section className="society-card"><h2>Admin Debug</h2><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={societyId ? `/societies/${societyId}` : "/societies"}>Back to Society dashboard</Link></div>
  </main>;
}
