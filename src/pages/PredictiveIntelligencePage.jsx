import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPredictiveIntelligence } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const list = (items, render = (x) => x, empty = "None found") => items?.length ? <ul>{items.map((x, i) => <li key={`${x.id || x}-${i}`}>{render(x)}</li>)}</ul> : <p>{empty}</p>;
const sections = [
  ["High Confidence Predictions", "high_confidence_predictions"], ["Improving Trends", "improving_trends"], ["Declining Trends", "declining_trends"], ["Emerging Risks", "emerging_risks"], ["Future Opportunities", "future_opportunities"], ["Leadership Forecast", "leadership_forecast"], ["Institution Forecast", "institution_forecast"], ["Business Forecast", "business_forecast"], ["Trust Forecast", "trust_forecast"], ["Container Forecast", "container_forecast"],
];

function PredictionCard({ prediction }) {
  return <article className="society-card">
    <p className="society-kicker">{prediction.prediction_type} · {prediction.trend}</p>
    <h2>{prediction.title}</h2>
    <p><strong>Probability:</strong> {prediction.probability}% · <strong>Confidence:</strong> {prediction.confidence} · <strong>Severity:</strong> {prediction.severity}</p>
    <p><strong>Time Horizon:</strong> {prediction.timeframe}</p>
    <p><strong>Prediction Explanation:</strong> {prediction.explanation}</p>
    <p className="society-muted">Trend: {prediction.trend_explanation}</p>
    <details><summary>Evidence and safeguards</summary>
      <h3>Evidence</h3>{list(prediction.evidence)}
      <h3>Missing Evidence</h3>{list(prediction.missing_evidence)}
      <h3>Assumptions</h3>{list(prediction.assumptions)}
      <p><strong>Related members:</strong> {(prediction.related_members || []).join(", ") || "None"}</p>
      <p><strong>Related roles:</strong> {(prediction.related_roles || []).join(", ") || "None"}</p>
      <p><strong>Related societies:</strong> {(prediction.related_societies || []).join(", ") || "None"}</p>
      <p><strong>Related institutions:</strong> {(prediction.related_institutions || []).join(", ") || "None"}</p>
      <p><strong>Related opportunities:</strong> {(prediction.related_opportunities || []).join(", ") || "None"}</p>
      <p><strong>Manual review:</strong> {prediction.requires_manual_review ? "Required" : "No"}</p>
      <p><strong>No workflow executed:</strong> {prediction.no_workflow_executed ? "Yes" : "No"}</p>
    </details>
  </article>;
}

export default function PredictiveIntelligencePage({ user, rbac }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { if (isAdmin) getPredictiveIntelligence(societyId, true).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin]);
  if (!isAdmin) return <main className="society-builder-shell"><h1>Predictive Intelligence</h1><p className="society-warning">Admin debug permission is required.</p></main>;
  if (!data) return <main className="society-builder-shell"><p>Loading Predictive Intelligence...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const d = data.dashboard || {};
  return <main className="society-builder-shell">
    <p className="society-kicker">Predictive Intelligence</p>
    <h1>Read-only forecast layer</h1>
    <p>Deterministic forecasts from existing Member, Society, Institution, and Opportunity Intelligence. No AI hallucination, machine learning, persistence, workflow execution, assignments, appointments, or notifications.</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">
      <article className="society-card"><h2>Overall Forecast</h2><p>Societies reviewed: {data.overall_forecast?.societies_reviewed}</p><p>Predictions: {data.overall_forecast?.prediction_count}</p><p>Confidence: {data.overall_forecast?.confidence}</p></article>
      <article className="society-card"><h2>Read-only Boundary</h2>{list(data.warnings)}</article>
    </section>
    <section className="society-card"><h2>All Predictions</h2><div className="society-grid">{(data.predictions || []).map((p) => <PredictionCard key={p.id} prediction={p} />)}</div></section>
    {sections.map(([title, key]) => <section className="society-card" key={key}><h2>{title}</h2><div className="society-grid">{(d[key] || []).map((p) => <PredictionCard key={p.id} prediction={p} />)}</div>{!(d[key] || []).length ? <p>No matching predictions.</p> : null}</section>)}
    <div className="society-actions"><Link className="society-btn secondary" to={societyId ? `/societies/${societyId}` : "/societies"}>Back to Society dashboard</Link></div>
  </main>;
}
