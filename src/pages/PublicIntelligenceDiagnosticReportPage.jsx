import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getPublicIntelligenceDiagnosticReport } from "../api/societyBuilder";

const PUBLIC_REPORT_TIMEOUT_MS = 30000;
const asArray = (value) => (Array.isArray(value) ? value : []);
const safeObject = (value) => (value && typeof value === "object" && !Array.isArray(value) ? value : {});
const safeText = (value, fallback = "Unavailable") => (typeof value === "string" && value.trim() ? value : fallback);

const withTimeout = (promise) => {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error("Public diagnostic report request timed out.")), PUBLIC_REPORT_TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer));
};

const publicErrorMessage = (err) => {
  const message = err?.message || "Report unavailable";
  if (/expired/i.test(message)) return "This public diagnostic report has expired.";
  if (/404|not found|invalid/i.test(message)) return "This public diagnostic report link is invalid or no longer available.";
  if (/timed out/i.test(message)) return "The public diagnostic report took too long to load. Please try again later.";
  return "This public diagnostic report could not be loaded safely.";
};

const normalizePublicReport = (payload) => {
  const report = safeObject(payload?.report || payload?.public_report || payload);
  const layers = asArray(report.layers).filter((layer) => layer && typeof layer === "object");
  return { ...report, layers };
};

function PublicReportError({ message }) {
  return <main className="cosmic-section"><h1>Public diagnostic report unavailable</h1><p>{message}</p></main>;
}

export default function PublicIntelligenceDiagnosticReportPage() {
  const { token } = useParams();
  const [state, setState] = useState({ loading: true, error: "", report: null });

  useEffect(() => {
    let active = true;
    if (!token || typeof token !== "string" || !token.trim()) {
      setState({ loading: false, error: "This public diagnostic report link is missing a token.", report: null });
      return () => { active = false; };
    }

    setState({ loading: true, error: "", report: null });
    withTimeout(getPublicIntelligenceDiagnosticReport(token))
      .then((payload) => {
        if (!active) return;
        const report = normalizePublicReport(payload);
        if (!Object.keys(report).length) {
          setState({ loading: false, error: "This public diagnostic report is malformed or empty.", report: null });
          return;
        }
        setState({ loading: false, error: "", report });
      })
      .catch((err) => {
        if (active) setState({ loading: false, error: publicErrorMessage(err), report: null });
      });
    return () => { active = false; };
  }, [token]);

  if (state.loading) return <main className="cosmic-section"><h1>Loading public diagnostic report…</h1></main>;
  if (state.error) return <PublicReportError message={state.error} />;

  const report = normalizePublicReport(state.report);
  const layers = report.layers;
  const health = safeObject(report.overall_health);
  const regressionSummary = safeObject(report.regression_summary);
  const noWriteConfirmation = safeObject(report.no_write_confirmation);
  const dependencyImpact = safeObject(report.dependency_impact);
  const dependencyChain = asArray(dependencyImpact.chain);

  return (
    <main className="cosmic-section intelligence-health-monitor" aria-labelledby="public-intel-report-title">
      <p className="section-kicker">Public · Read-Only · Sanitized Fixture Diagnostics</p>
      <h1 id="public-intel-report-title">Intelligence Diagnostic Report</h1>
      <p>{safeText(report.overall_summary, "Overall summary unavailable.")}</p><p>{safeText(report.source_note, "This public report is sanitized and read-only.")}</p>
      <div className="dashboard-grid">
        <article className="stat-card"><h2>{health.percent ?? "—"}%</h2><p>Overall health</p></article>
        <article className="stat-card"><h2>{regressionSummary.count ?? 0}</h2><p>Regressions</p></article>
        <article className="stat-card"><h2>{asArray(report.failed_layers).length}</h2><p>Failed layers</p></article>
        <article className="stat-card"><h2>{asArray(report.warnings).length}</h2><p>Warnings</p></article>
      </div>
      <section className="stat-card"><h2>Read-only/no-write confirmation</h2><p>Production writes: {noWriteConfirmation.production_writes ?? 0}</p><p>Workflow execution: {noWriteConfirmation.workflow_execution ? "Yes" : "No"}</p><p>Notifications: {noWriteConfirmation.notification_count ?? 0}</p><p>Assignments: {noWriteConfirmation.assignment_count ?? 0}</p><p>Persisted intelligence outputs: {noWriteConfirmation.persistence_of_intelligence_outputs ? "Yes" : "No"}</p></section>
      <section><h2>Layer-by-layer status</h2><div className="dashboard-grid">{layers.length ? layers.map((layer, index) => {
        const expected = safeObject(layer.expected);
        const actual = safeObject(layer.actual);
        return <article className="stat-card" key={layer.layer || `public-layer-${index}`}><h3>{safeText(layer.layer, "Unknown Layer")}</h3><p>Status: <strong>{safeText(layer.status, "UNKNOWN")}</strong></p><p>Expected score: {expected.score ?? "—"} · Actual score: {actual.score ?? "—"}</p><p>Regression: {layer.regression_level || layer.regression || "None"}</p><p>Explanation: {safeText(layer.why_this_changed || layer.plain_language_reason || layer.explanation, "Layer details are unavailable in this public report.")}</p></article>;
      }) : <article className="stat-card"><h3>Layer data unavailable</h3><p>This public report did not include layer-by-layer details.</p></article>}</div></section>
      <section className="dashboard-grid">
        <article className="stat-card"><h2>Dependency Impact</h2>{dependencyChain.length ? dependencyChain.map((item) => <p key={item.layer}><strong>{safeText(item.layer, "Unknown Layer")}</strong>: {safeText(item.state, "stable")}</p>) : <p>Dependency impact unavailable.</p>}</article>
        <article className="stat-card"><h2>Regression Summary</h2><p>Regression count: {regressionSummary.count ?? 0}</p>{asArray(regressionSummary.layers).map((item) => <p key={item.layer}>{safeText(item.layer)}: {safeText(item.regression, "None")}</p>)}</article>
        <article className="stat-card"><h2>Fixture</h2><p>{safeText(report.fixture_name)} · {safeText(report.fixture_version)}</p><p>Generated: {safeText(report.generated_at)}</p><p>Expires: {safeText(report.expires_at)}</p></article>
      </section>
    </main>
  );
}
