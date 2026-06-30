import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getSocietyIntelligence } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const scoreLine = (score) => score ? `${score.score} — ${score.why}` : "Missing";
const list = (items, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.action || x}-${i}`}>{x.action ? <><strong>{x.action}</strong>: {x.why}</> : x}</li>)}</ul> : <p>{empty}</p>;

export default function SocietyIntelligenceDashboardPage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getSocietyIntelligence(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!data) return <main className="society-builder-shell"><p>Loading Society Intelligence...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const s = data.scores || {};
  return <main className="society-builder-shell">
    <p className="society-kicker">Society Intelligence</p>
    <h1>{data.society_name}</h1>
    <p>{data.software_boundary}</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Overall Health</h2><p><strong>{scoreLine(data.overall_health)}</strong></p><p>Confidence: {data.confidence}</p></article>
      <article className="society-card"><h2>Trust</h2><p>{scoreLine(s.trust_score)}</p></article>
      <article className="society-card"><h2>Participation</h2><p>{scoreLine(s.participation_score)}</p></article>
      <article className="society-card"><h2>Leadership Coverage</h2><p>{scoreLine(s.leadership_coverage)}</p></article>
      <article className="society-card"><h2>Business Readiness</h2><p>{scoreLine(s.business_readiness)}</p></article>
      <article className="society-card"><h2>Assessment Completion</h2><p>{scoreLine(s.assessment_completion)}</p></article>
      <article className="society-card"><h2>Missing Roles</h2>{list(data.missing_roles)}</article>
      <article className="society-card"><h2>Recommended Next Actions</h2>{list(data.recommended_next_steps)}</article>
    </section>
    <section className="society-grid"><article className="society-card"><h2>Top Risks</h2>{list(data.top_risks)}</article><article className="society-card"><h2>Top Strengths</h2>{list(data.top_strengths)}</article><article className="society-card"><h2>Warnings</h2>{list(data.warnings)}</article></section>
    {isAdmin && data.debug ? <section className="society-card"><h2>Admin Debug Mode</h2><p>Only admins can inspect raw Society Intelligence JSON, score calculations, evidence sources, confidence calculations, fallback reasons, and missing evidence.</p><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={`/societies/${societyId}`}>Back to Society Home</Link></div>
  </main>;
}
