import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getInstitutionIntelligence } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const scoreLine = (score) => score ? `${score.score} — ${score.why}` : "Missing";
const list = (items, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.action || x.level || x}-${i}`}>{x.action ? <><strong>{x.action}</strong>: {x.why}</> : x.level ? <><strong>{x.level}</strong>: {x.why}</> : x}</li>)}</ul> : <p>{empty}</p>;
const card = (title, score) => <article className="society-card"><h2>{title}</h2><p>{scoreLine(score)}</p><p className="society-muted">{score?.calculation}</p></article>;

export default function SocietyIntelligenceDashboardPage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getInstitutionIntelligence(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!data) return <main className="society-builder-shell"><p>Loading Institution Intelligence...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const s = data.scores || {};
  return <main className="society-builder-shell">
    <p className="society-kicker">Institution Intelligence</p>
    <h1>{data.institution_name}</h1>
    <p>{data.source_of_truth_boundary}</p>
    <p className="society-muted">Hierarchy: {(data.intelligence_hierarchy || []).join(" ↓ ")}</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Institution Health</h2><p><strong>{scoreLine(data.institution_health)}</strong></p><p>Confidence: {data.confidence}</p><p>Health trend: {data.health_trend?.why}</p></article>
      {card("Leadership Health", s.leadership_health)}
      {card("Participation Health", s.participation_health)}
      {card("Trust Health", s.trust_health)}
      {card("Knowledge Health", s.knowledge_health)}
      {card("Financial Readiness", s.financial_readiness)}
      {card("Operational Readiness", s.operational_readiness)}
      {card("Business Readiness", s.business_readiness)}
      {card("Volunteer Capacity", s.volunteer_capacity)}
      {card("Role Coverage", s.role_coverage)}
      {card("Assessment Coverage", s.assessment_coverage)}
      {card("Container Progress", s.container_completion)}
      <article className="society-card"><h2>Risk Level</h2>{list([data.risk_level])}</article>
      <article className="society-card"><h2>Growth Potential</h2><p>{scoreLine(data.growth_potential)}</p></article>
      <article className="society-card"><h2>Missing Roles</h2>{list(data.missing_evidence?.filter((x) => ["Facilitator", "Treasurer", "Assistant Treasurer", "Recordkeeper", "Care Coordinator"].includes(x)))}</article>
      <article className="society-card"><h2>Recommendations</h2>{list(data.recommended_next_actions)}</article>
    </section>
    <section className="society-grid"><article className="society-card"><h2>Risks</h2>{list(data.institution_weaknesses)}</article><article className="society-card"><h2>Strengths</h2>{list(data.institution_strengths)}</article><article className="society-card"><h2>Warnings</h2>{list(data.warnings)}</article></section>
    <section className="society-card"><h2>Evidence & Confidence</h2><p>{data.calculation_explanation}</p><p><strong>Confidence:</strong> {data.confidence}</p>{list((data.evidence || []).map((e) => `${e.system}: ${e.summary}`), "No evidence found")}</section>
    {isAdmin && data.debug ? <section className="society-card"><h2>Admin Debug Mode</h2><p>Only admins can inspect raw Institution Intelligence JSON, evidence, calculations, confidence, fallback reasons, and missing evidence.</p><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={`/societies/${societyId}`}>Back to Institution Home</Link></div>
  </main>;
}
