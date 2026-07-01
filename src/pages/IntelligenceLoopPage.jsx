import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getExecutionIntelligence, getInstitutionalLearning, getInstitutionalMemory } from "../api/societyBuilder";
import { isAdminUser } from "../authz";

const CONFIG = {
  execution: { title: "Execution Intelligence", kicker: "Phase 10 · Execution Intelligence", load: getExecutionIntelligence, fields: ["execution_score", "success_score", "completion_percentage", "confidence"], listFields: ["bottlenecks", "delays", "missed_milestones", "over_performing_areas", "under_performing_areas", "recommended_lessons_learned"] },
  memory: { title: "Institutional Memory", kicker: "Phase 11 · Institutional Memory", load: getInstitutionalMemory, fields: ["memory_count", "confidence", "search"], listFields: ["evidence", "missing_evidence", "assumptions"] },
  learning: { title: "Institutional Learning", kicker: "Phase 12 · Institutional Learning", load: getInstitutionalLearning, fields: ["confidence"], listFields: ["lessons_learned", "improvement_recommendations", "recurring_themes", "common_bottlenecks", "recommended_best_practices"] },
};

const list = (items, render = (x) => x) => items?.length ? <ul>{items.map((item, index) => <li key={`${String(item)}-${index}`}>{render(item)}</li>)}</ul> : <p>No records found.</p>;

function MemoryRecords({ memories }) {
  return <section className="society-card"><h2>Searchable Historical Records</h2>{memories?.length ? memories.map((memory) => <article className="society-card" key={memory.id}><p className="society-kicker">{memory.type} · {memory.timestamp}</p><h3>{memory.decision_summary}</h3><p><strong>Reason:</strong> {memory.reason}</p><p><strong>Expected:</strong> {memory.expected_outcome}</p><p><strong>Actual:</strong> {memory.actual_outcome || "Not available"}</p><details><summary>Links and evidence</summary><pre>{JSON.stringify(memory, null, 2)}</pre></details></article>) : <p>No memory records found.</p>}</section>;
}

export default function IntelligenceLoopPage({ user, rbac, layer }) {
  const { societyId } = useParams();
  const isAdmin = isAdminUser(user, rbac);
  const config = CONFIG[layer];
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { if (isAdmin && config) config.load(societyId, isAdmin).then(setData).catch((e) => setError(e.message)); }, [societyId, isAdmin, config]);
  if (!config) return <main className="society-builder-shell"><h1>Unknown intelligence layer</h1></main>;
  if (!isAdmin) return <main className="society-builder-shell"><h1>{config.title}</h1><p className="society-warning">Admin permission is required.</p></main>;
  if (!data) return <main className="society-builder-shell"><p>Loading {config.title}...</p>{error && <p className="society-warning">{error}</p>}</main>;
  return <main className="society-builder-shell">
    <p className="society-kicker">{config.kicker}</p><h1>{config.title}</h1>
    <p className="society-warning">Read-only advisory intelligence. No records, workflows, notifications, Kanban cards, assignments, roles, permissions, events, or financial records are changed.</p>
    {error && <p className="society-warning">{error}</p>}
    <section className="society-grid">{config.fields.map((field) => <article className="society-card" key={field}><h2>{field.replaceAll("_", " ")}</h2><p>{String(data[field] ?? "—")}</p></article>)}</section>
    {data.variance_analysis ? <section className="society-card"><h2>Variance Analysis</h2><pre>{JSON.stringify(data.variance_analysis, null, 2)}</pre></section> : null}
    {config.listFields.map((field) => <section className="society-card" key={field}><h2>{field.replaceAll("_", " ")}</h2>{list(data[field])}</section>)}
    {layer === "memory" ? <MemoryRecords memories={data.memories} /> : null}
    {data.debug ? <section className="society-card"><h2>Admin Debug</h2><pre>{JSON.stringify(data.debug, null, 2)}</pre></section> : null}
    <div className="society-actions"><Link className="society-btn secondary" to={societyId ? `/societies/${societyId}` : "/societies"}>Back to Society dashboard</Link></div>
  </main>;
}
