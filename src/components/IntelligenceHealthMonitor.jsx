import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { generatePublicIntelligenceDiagnosticReport, getIntelligenceHealthHistory, runIntelligenceHealthDiagnostic } from "../api/societyBuilder";

const DIAGNOSTIC_TIMEOUT_MS = 30000;
const DEBUG_ERRORS = import.meta.env?.DEV || import.meta.env?.VITE_ADMIN_DEBUG === "true";

const withTimeout = (promise, message = "Diagnostic request timed out. Please try again.") => {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error(message)), DIAGNOSTIC_TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer));
};

const asArray = (value) => (Array.isArray(value) ? value : []);
const safeObject = (value) => (value && typeof value === "object" ? value : {});
const adminErrorMessage = (fallback, err) => `${fallback}${DEBUG_ERRORS && err?.message ? ` (${err.message})` : ""}`;
const normalizeHistory = (payload) => asArray(payload?.history).filter((run) => run && typeof run === "object");
const normalizeReport = (payload) => safeObject(payload?.report || payload?.public_report || payload);

const statusIcon = (layer) => {
  if (layer?.status === "FAIL") return "🔴 Failure";
  if (layer?.regression) return "🟠 Regression";
  if (layer?.status === "WARNING") return "🟡 Warning";
  return "🟢 Healthy";
};

export default function IntelligenceHealthMonitor() {
  const mountedRef = useRef(true);
  const [running, setRunning] = useState(false);
  const [diagnostic, setDiagnostic] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [reportError, setReportError] = useState("");
  const [publicReport, setPublicReport] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const loadHistory = useCallback(async () => {
    try {
      const res = await withTimeout(getIntelligenceHealthHistory(), "Diagnostic history request timed out.");
      if (!mountedRef.current) return [];
      const safeHistory = normalizeHistory(res);
      setHistory(safeHistory);
      setHistoryError(safeHistory.length ? "" : "Last run could not be loaded");
      return safeHistory;
    } catch (err) {
      if (!mountedRef.current) return [];
      setHistory([]);
      setHistoryError(adminErrorMessage("Last run could not be loaded", err));
      return [];
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    loadHistory();
    return () => { mountedRef.current = false; };
  }, [loadHistory]);

  const run = async () => {
    if (running || generatingReport) return;
    setRunning(true); setError(""); setReportError("");
    try {
      const res = await withTimeout(runIntelligenceHealthDiagnostic());
      if (!mountedRef.current) return;
      setDiagnostic(safeObject(res));
      await loadHistory();
    } catch (err) {
      if (mountedRef.current) setError(adminErrorMessage("Diagnostics unavailable", err));
    } finally {
      if (mountedRef.current) setRunning(false);
    }
  };

  const generateReport = async () => {
    if (running || generatingReport) return;
    setGeneratingReport(true); setError(""); setReportError("");
    try {
      const res = await withTimeout(generatePublicIntelligenceDiagnosticReport(), "Public report generation timed out.");
      if (!mountedRef.current) return;
      const report = normalizeReport(res);
      if (!report?.token) throw new Error("Public report response did not include a token.");
      setPublicReport(report);
      await loadHistory();
    } catch (err) {
      if (mountedRef.current) setReportError(adminErrorMessage("Public report could not be generated", err));
    } finally {
      if (mountedRef.current) setGeneratingReport(false);
    }
  };

  const result = safeObject(diagnostic || history[0]);
  const layers = asArray(result?.layers).filter((layer) => layer && typeof layer === "object");
  const publicUrl = publicReport?.token ? `${window.location.origin}/public/intelligence-diagnostics/${publicReport.token}` : "";
  const healthTrend = useMemo(() => safeObject(result?.comparison_to_previous || result?.health_trend), [result]);
  const actionDisabled = running || generatingReport;

  return (
    <section className="cosmic-section intelligence-health-monitor" aria-labelledby="intelligence-health-title">
      <p className="section-kicker">Admin Only · Read-Only Diagnostic</p>
      <h2 id="intelligence-health-title">🧠 Intelligence Health Monitor</h2>
      <p className="admin-subtext">Runs deterministic isolated fixtures through Member, Society, Institution, Opportunity, Predictive, Decision Support, Execution Planning, Execution Intelligence, Institutional Memory, and Institutional Learning layers without touching production records, workflow tasks, assignments, notifications, calendars, payments, businesses, or persisted intelligence outputs.</p>
      <div className="hero-actions">
        <button className="hero-btn" type="button" onClick={run} disabled={actionDisabled}>{running ? "Running Full Intelligence Diagnostic..." : "Run Full Intelligence Diagnostic"}</button>
        <button className="hero-btn secondary" type="button" onClick={generateReport} disabled={actionDisabled}>{generatingReport ? "Generating Public Report..." : "Generate Public Diagnostic Report"}</button>
      </div>
      {publicUrl && <article className="stat-card"><h3>Public Diagnostic Report</h3><p>This URL is public, read-only, sanitized, fixture-only, and expires at {publicReport?.expires_at || "the configured expiration time"}.</p><input readOnly value={publicUrl} onFocus={(event) => event.target.select()} aria-label="Public diagnostic report URL" /><button type="button" onClick={() => navigator.clipboard?.writeText(publicUrl)}>Copy public URL</button></article>}
      {error && <article className="stat-card admin-error"><h3>Diagnostics unavailable</h3><p>⚠️ {error}</p></article>}
      {reportError && <article className="stat-card admin-error"><h3>Public report could not be generated</h3><p>⚠️ {reportError}</p></article>}
      {historyError && !layers.length && <article className="stat-card"><h3>Last run could not be loaded</h3><p>Diagnostics unavailable</p></article>}

      <div className="dashboard-grid">
        <div className="stat-card"><h3>Overall Health</h3><h2>{(result?.overall_health_percent ?? result?.overall_health?.percent) ?? "—"}%</h2></div>
        <div className="stat-card"><h3>Regression Count</h3><h2>{result?.regression_count ?? result?.regression_summary?.count ?? 0}</h2></div>
        <div className="stat-card"><h3>Warnings</h3><h2>{asArray(result?.warnings).length}</h2></div>
        <div className="stat-card"><h3>Critical Failures</h3><h2>{asArray(result?.critical_failures).length || asArray(result?.failed_layers).length}</h2></div>
        <div className="stat-card"><h3>Last Successful Diagnostic</h3><p>{result?.last_successful_diagnostic || "No previous successful run"}</p></div>
        <div className="stat-card"><h3>Health Trend</h3><p>{healthTrend.available ? `${healthTrend.health_trend > 0 ? "+" : ""}${healthTrend.health_trend}%` : "No previous run"}</p></div>
      </div>

      <h3>Layer Status</h3>
      <div className="dashboard-grid">
        {layers.length ? layers.map((layer, index) => {
          const expected = safeObject(layer.expected);
          const actual = safeObject(layer.actual);
          const confidence = safeObject(layer.confidence_difference);
          const priority = safeObject(layer.priority_difference);
          return (
            <article className="stat-card" key={layer.layer || `layer-${index}`}>
              <h3>{layer.layer || "Unknown Layer"}</h3>
              <p><strong>{statusIcon(layer)}</strong></p>
              <p>Health: <strong>{statusIcon(layer)}</strong></p>
              <p>Status: <strong>{layer.status || "UNKNOWN"}</strong></p>
              <p>Execution Time: <strong>{layer.execution_time_ms ?? "—"}ms</strong></p>
              <p>Version: <strong>v1</strong></p>
              <p>Diagnostics: <strong>{layer.explanation || "Diagnostics unavailable"}</strong></p>
              <p>Regression: <strong>{layer.regression || "None"}</strong></p>
              <p>Expected: {expected.score ?? "—"} · Actual: {actual.score ?? "—"}</p>
              <p>Confidence: {confidence.expected ?? "—"} → {confidence.actual ?? "—"}</p>
              <p>Missing Evidence Δ: {layer.missing_evidence_difference ?? "—"}</p>
              <p>Priority: {priority.expected ?? "—"} → {priority.actual ?? "—"}</p>
              <p>{layer.explanation || "Diagnostics unavailable"}</p>
            </article>
          );
        }) : <article className="stat-card"><h3>Diagnostics unavailable</h3><p>Layer data is missing or could not be loaded.</p></article>}
      </div>

      <div className="dashboard-grid">
        <article className="stat-card"><h3>Regression Summary</h3>{layers.filter((l) => l.regression).length ? layers.filter((l) => l.regression).map((l) => <p key={l.layer}>{l.layer}: {l.regression} ({safeObject(l.difference_summary).score ?? "—"})</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Critical Failures</h3>{asArray(result?.critical_failures).length ? asArray(result.critical_failures).map((l, i) => <p key={l.layer || i}>{l.layer || "Unknown Layer"}: {l.explanation || "Diagnostics unavailable"}</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Performance Metrics</h3><pre className="data-note">{JSON.stringify(result?.performance || result?.performance_timings || {}, null, 2)}</pre></article>
        <article className="stat-card"><h3>Root Cause Analysis</h3>{asArray(result?.root_cause_analysis).length ? asArray(result.root_cause_analysis).map((line) => <p key={line}>{line}</p>) : <p>Run a diagnostic to view root-cause tracing.</p>}</article>
      </div>

      <h3>Diagnostic History</h3>
      <table className="admin-table"><thead><tr><th>Run</th><th>Health</th><th>Regressions</th><th>Execution Time</th><th>Safety</th></tr></thead><tbody>{history.length ? history.map((run, index) => <tr key={run.diagnostic_id || index}><td>{run.created_at || "Last run could not be loaded"}</td><td>{run.overall_health_percent ?? run.overall_health?.percent ?? "—"}%</td><td>{run.regression_count ?? run.regression_summary?.count ?? 0}</td><td>{run.performance?.total_execution_time_ms ?? run.performance_timings?.total_execution_time_ms ?? "—"}ms</td><td>{run.production_writes === 0 && !run.workflow_execution ? "Read-only" : "Review required"}</td></tr>) : <tr><td colSpan={5}>No diagnostic history yet.</td></tr>}</tbody></table>

      <h3>Compare Previous Run</h3>
      <pre className="data-note">{JSON.stringify(healthTrend, null, 2)}</pre>
      <h3>Debug Output</h3>
      <pre className="data-note">{JSON.stringify(layers.map(({ layer, debug_payload }) => ({ layer, debug_payload })), null, 2)}</pre>
    </section>
  );
}
