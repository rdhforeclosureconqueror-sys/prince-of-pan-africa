import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getPublicIntelligenceDiagnosticReport } from "../api/societyBuilder";

export default function PublicIntelligenceDiagnosticReportPage() {
  const { token } = useParams();
  const [state, setState] = useState({ loading: true, error: "", report: null });

  useEffect(() => {
    getPublicIntelligenceDiagnosticReport(token)
      .then((report) => setState({ loading: false, error: "", report }))
      .catch((err) => setState({ loading: false, error: err.message || "Report unavailable", report: null }));
  }, [token]);

  if (state.loading) return <main className="cosmic-section"><h1>Loading public diagnostic report…</h1></main>;
  if (state.error) return <main className="cosmic-section"><h1>Public diagnostic report unavailable</h1><p>{state.error}</p></main>;

  const report = state.report;
  return (
    <main className="cosmic-section intelligence-health-monitor" aria-labelledby="public-intel-report-title">
      <p className="section-kicker">Public · Read-Only · Sanitized Fixture Diagnostics</p>
      <h1 id="public-intel-report-title">Intelligence Diagnostic Report</h1>
      <p>{report.source_note}</p>
      <div className="dashboard-grid">
        <article className="stat-card"><h2>{report.overall_health?.percent}%</h2><p>Overall health</p></article>
        <article className="stat-card"><h2>{report.regression_summary?.count || 0}</h2><p>Regressions</p></article>
        <article className="stat-card"><h2>{report.failed_layers?.length || 0}</h2><p>Failed layers</p></article>
        <article className="stat-card"><h2>{report.warnings?.length || 0}</h2><p>Warnings</p></article>
      </div>
      <section className="stat-card"><h2>Read-only boundary</h2><pre className="data-note">{JSON.stringify(report.no_write_confirmation, null, 2)}</pre></section>
      <section><h2>Layer-by-layer status</h2><div className="dashboard-grid">{(report.layers || []).map((layer) => <article className="stat-card" key={layer.layer}><h3>{layer.layer}</h3><p>Status: <strong>{layer.status}</strong></p><p>Expected score: {layer.expected?.score} · Actual score: {layer.actual?.score}</p><p>Regression: {layer.regression || "None"}</p><p>Execution time: {layer.execution_time_ms}ms</p><p>{layer.explanation}</p></article>)}</div></section>
      <section className="dashboard-grid">
        <article className="stat-card"><h2>Regression Summary</h2><pre className="data-note">{JSON.stringify(report.regression_summary, null, 2)}</pre></article>
        <article className="stat-card"><h2>Performance Timings</h2><pre className="data-note">{JSON.stringify(report.performance_timings, null, 2)}</pre></article>
        <article className="stat-card"><h2>Fixture</h2><p>{report.fixture_name} · {report.fixture_version}</p><p>Generated: {report.generated_at}</p><p>Expires: {report.expires_at}</p></article>
      </section>
    </main>
  );
}
