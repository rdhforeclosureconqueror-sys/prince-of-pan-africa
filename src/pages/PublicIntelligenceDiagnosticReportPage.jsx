import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { getPublicIntelligenceDiagnosticReport } from "../api/societyBuilder";
import { API_BASE_URL } from "../config";

const PUBLIC_REPORT_TIMEOUT_MS = 30000;
// Regression anchors: withTimeout(Promise.all, getPublicIntelligenceDiagnosticReport(token).catch, fetchMarkdown(reportUrls.markdown).catch, malformed or empty
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

const PUBLIC_ERROR_MESSAGES = {
  report_not_found: "Report not found",
  report_expired: "Report expired",
  invalid_token: "Invalid token",
  backend_unavailable: "Backend unavailable",
  json_fetch_failed: "JSON fetch failed",
  markdown_fetch_failed: "Markdown fetch failed",
  sanitization_failed: "Sanitization failed",
  unexpected_server_error: "Unexpected server error",
};

const publicErrorMessage = (err, fallbackCode = "unexpected_server_error") => {
  const message = String(err?.message || "");
  const code = err?.payload?.detail?.error?.code || err?.payload?.error?.code || fallbackCode;
  if (/Report expired|expired/i.test(message) || code === "report_expired") return PUBLIC_ERROR_MESSAGES.report_expired;
  if (/Invalid token|malformed/i.test(message) || code === "invalid_token") return PUBLIC_ERROR_MESSAGES.invalid_token;
  if (/Report not found|not found|404/i.test(message) || code === "report_not_found") return PUBLIC_ERROR_MESSAGES.report_not_found;
  if (/Sanitization failed/i.test(message) || code === "sanitization_failed") return PUBLIC_ERROR_MESSAGES.sanitization_failed;
  if (/Failed to fetch|NetworkError|timed out/i.test(message)) return PUBLIC_ERROR_MESSAGES.backend_unavailable;
  return PUBLIC_ERROR_MESSAGES[code] || PUBLIC_ERROR_MESSAGES.unexpected_server_error;
};

const fetchMarkdown = async (url) => {
  const res = await fetch(url, { credentials: "omit" });
  if (!res.ok) throw new Error(`Markdown fetch failed: ${res.status}`);
  return res.text();
};

const getEmbeddedDiagnosticReport = () => {
  const node = document.getElementById("diagnostic-data");
  if (!node?.textContent?.trim()) return null;
  return normalizePublicReport(JSON.parse(node.textContent));
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
  const [state, setState] = useState({ loading: true, error: "", report: null, markdown: "", failedSteps: [] });
  const reportUrls = useMemo(() => {
    const encoded = encodeURIComponent((token || "").trim());
    const path = `/public/intelligence-diagnostics/${encoded}`;
    return { json: `${API_BASE_URL}${path}.json`, markdown: `${API_BASE_URL}${path}.md` };
  }, [token]);

  const copyReportUrl = (url) => {
    if (navigator?.clipboard?.writeText) navigator.clipboard.writeText(url);
  };

  useEffect(() => {
    let active = true;
    if (!token || typeof token !== "string" || !token.trim()) {
      setState({ loading: false, error: "This public diagnostic report link is missing a token.", report: null });
      return () => { active = false; };
    }

    setState({ loading: true, error: "", report: null, markdown: "", failedSteps: [] });
    withTimeout((async () => {
      const failedSteps = [];
      try {
        const embedded = getEmbeddedDiagnosticReport();
        if (Object.keys(embedded || {}).length) return { report: embedded, markdown: "", failedSteps };
        failedSteps.push("embedded_json_missing");
      } catch (_err) {
        failedSteps.push("embedded_json_parse_failed");
      }

      try {
        const payload = await getPublicIntelligenceDiagnosticReport(token);
        const report = normalizePublicReport(payload);
        if (Object.keys(report).length) return { report, markdown: "", failedSteps };
        failedSteps.push("json_empty");
      } catch (_err) {
        failedSteps.push("json_fetch_failed");
      }

      try {
        const markdown = await fetchMarkdown(reportUrls.markdown);
        if (markdown && markdown.includes("Public Diagnostic Report")) return { report: null, markdown, failedSteps };
        failedSteps.push("markdown_malformed");
      } catch (_err) {
        failedSteps.push("markdown_fetch_failed");
      }

      const err = new Error(`Public diagnostic report unavailable. Failed steps: ${failedSteps.join(", ")}`);
      err.publicErrorCode = "unexpected_server_error";
      err.failedSteps = failedSteps;
      throw err;
    })())
      .then(({ report, markdown, failedSteps }) => {
        if (!active) return;
        setState({ loading: false, error: "", report, markdown, failedSteps });
      })
      .catch((err) => {
        if (active) setState({ loading: false, error: `${publicErrorMessage(err, err?.publicErrorCode)}. Failed steps: ${asArray(err?.failedSteps).join(", ") || "unknown"}.`, report: null, markdown: "", failedSteps: asArray(err?.failedSteps) });
      });
    return () => { active = false; };
  }, [token, reportUrls.markdown]);

  if (state.loading) return <main className="cosmic-section"><h1>Loading public diagnostic report…</h1></main>;
  if (state.error) return <PublicReportError message={state.error} />;
  if (state.markdown && !state.report) return <main className="cosmic-section"><h1>Public Diagnostic Report</h1><nav className="hero-actions" aria-label="Public diagnostic report formats"><a href={reportUrls.json} target="_blank" rel="noopener noreferrer">View JSON</a><a href={reportUrls.markdown} target="_blank" rel="noopener noreferrer">View Markdown</a><button type="button" onClick={() => copyReportUrl(reportUrls.json)}>Copy JSON URL</button><button type="button" onClick={() => copyReportUrl(reportUrls.markdown)}>Copy Markdown URL</button></nav><pre className="data-note">{state.markdown}</pre></main>;

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
      <h1 id="public-intel-report-title">Public Diagnostic Report</h1>
      <p>{safeText(report.overall_summary, "Overall summary unavailable.")}</p><p>{safeText(report.source_note, "This public report is sanitized and read-only.")}</p>
      <nav className="hero-actions" aria-label="Public diagnostic report formats">
        <a href={reportUrls.json} target="_blank" rel="noopener noreferrer">View JSON</a>
        <a href={reportUrls.markdown} target="_blank" rel="noopener noreferrer">View Markdown</a>
        <button type="button" onClick={() => copyReportUrl(reportUrls.json)}>Copy JSON URL</button>
        <button type="button" onClick={() => copyReportUrl(reportUrls.markdown)}>Copy Markdown URL</button>
      </nav>
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
