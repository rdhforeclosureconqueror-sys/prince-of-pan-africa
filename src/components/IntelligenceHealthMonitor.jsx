import React, { useEffect, useMemo, useState } from "react";
import { getIntelligenceHealthHistory, runIntelligenceHealthDiagnostic } from "../api/societyBuilder";

const statusIcon = (layer) => {
  if (layer?.status === "FAIL") return "🔴 Failure";
  if (layer?.regression) return "🟠 Regression";
  if (layer?.status === "WARNING") return "🟡 Warning";
  return "🟢 Healthy";
};

export default function IntelligenceHealthMonitor() {
  const [running, setRunning] = useState(false);
  const [diagnostic, setDiagnostic] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  const loadHistory = async () => {
    const res = await getIntelligenceHealthHistory();
    setHistory(res.history || []);
  };

  useEffect(() => { loadHistory().catch(() => {}); }, []);

  const run = async () => {
    setRunning(true); setError("");
    try {
      const res = await runIntelligenceHealthDiagnostic();
      setDiagnostic(res); await loadHistory();
    } catch (err) {
      setError(err?.message || "Diagnostic failed.");
    } finally {
      setRunning(false);
    }
  };

  const result = diagnostic || history[0];
  const healthTrend = useMemo(() => result?.comparison_to_previous || {}, [result]);

  return (
    <section className="cosmic-section intelligence-health-monitor" aria-labelledby="intelligence-health-title">
      <p className="section-kicker">Admin Only · Read-Only Diagnostic</p>
      <h2 id="intelligence-health-title">🧠 Intelligence Health Monitor</h2>
      <p className="admin-subtext">Runs deterministic isolated fixtures through Member, Society, Institution, Opportunity, Predictive, Decision Support, and Execution Planning layers without touching production records, workflow tasks, assignments, notifications, calendars, payments, businesses, or persisted intelligence outputs.</p>
      <button className="hero-btn" type="button" onClick={run} disabled={running}>{running ? "Running Full Intelligence Diagnostic..." : "Run Full Intelligence Diagnostic"}</button>
      {error && <p className="admin-error">⚠️ {error}</p>}

      <div className="dashboard-grid">
        <div className="stat-card"><h3>Overall Health</h3><h2>{result?.overall_health_percent ?? "—"}%</h2></div>
        <div className="stat-card"><h3>Regression Count</h3><h2>{result?.regression_count ?? 0}</h2></div>
        <div className="stat-card"><h3>Warnings</h3><h2>{result?.warnings?.length ?? 0}</h2></div>
        <div className="stat-card"><h3>Critical Failures</h3><h2>{result?.critical_failures?.length ?? 0}</h2></div>
        <div className="stat-card"><h3>Last Successful Diagnostic</h3><p>{result?.last_successful_diagnostic || "No previous successful run"}</p></div>
        <div className="stat-card"><h3>Health Trend</h3><p>{healthTrend.available ? `${healthTrend.health_trend > 0 ? "+" : ""}${healthTrend.health_trend}%` : "No previous run"}</p></div>
      </div>

      <h3>Layer Status</h3>
      <div className="dashboard-grid">
        {(result?.layers || []).map((layer) => (
          <article className="stat-card" key={layer.layer}>
            <h3>{layer.layer}</h3>
            <p><strong>{statusIcon(layer)}</strong></p>
            <p>Execution Time: <strong>{layer.execution_time_ms}ms</strong></p>
            <p>Regression: <strong>{layer.regression || "None"}</strong></p>
            <p>Expected: {layer.expected.score} · Actual: {layer.actual.score}</p>
            <p>Confidence: {layer.confidence_difference.expected} → {layer.confidence_difference.actual}</p>
            <p>Missing Evidence Δ: {layer.missing_evidence_difference}</p>
            <p>Priority: {layer.priority_difference.expected} → {layer.priority_difference.actual}</p>
            <p>{layer.explanation}</p>
          </article>
        ))}
      </div>

      <div className="dashboard-grid">
        <article className="stat-card"><h3>Regression Summary</h3>{(result?.layers || []).filter((l) => l.regression).map((l) => <p key={l.layer}>{l.layer}: {l.regression} ({l.difference_summary.score})</p>) || "None"}</article>
        <article className="stat-card"><h3>Critical Failures</h3>{result?.critical_failures?.length ? result.critical_failures.map((l) => <p key={l.layer}>{l.layer}: {l.explanation}</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Performance Metrics</h3><pre className="data-note">{JSON.stringify(result?.performance || {}, null, 2)}</pre></article>
        <article className="stat-card"><h3>Root Cause Analysis</h3>{(result?.root_cause_analysis || ["Run a diagnostic to view root-cause tracing."]).map((line) => <p key={line}>{line}</p>)}</article>
      </div>

      <h3>Diagnostic History</h3>
      <table className="admin-table"><thead><tr><th>Run</th><th>Health</th><th>Regressions</th><th>Execution Time</th><th>Safety</th></tr></thead><tbody>{history.length ? history.map((run) => <tr key={run.diagnostic_id}><td>{run.created_at}</td><td>{run.overall_health_percent}%</td><td>{run.regression_count}</td><td>{run.performance?.total_execution_time_ms}ms</td><td>{run.production_writes === 0 && !run.workflow_execution ? "Read-only" : "Review required"}</td></tr>) : <tr><td colSpan={5}>No diagnostic history yet.</td></tr>}</tbody></table>

      <h3>Compare Previous Run</h3>
      <pre className="data-note">{JSON.stringify(healthTrend, null, 2)}</pre>
      <h3>Debug Output</h3>
      <pre className="data-note">{JSON.stringify(result?.layers?.map(({ layer, debug_payload }) => ({ layer, debug_payload })), null, 2)}</pre>
    </section>
  );
}
