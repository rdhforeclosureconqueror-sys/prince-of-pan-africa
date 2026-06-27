import React, { useEffect, useState } from "react";
import { api } from "../api/api";
import "../styles/mutualAid.css";

const emptyOps = {
  health: {}, request_lifecycle: {}, review_metrics: {}, decision_metrics: {}, appeal_metrics: {},
  notification_delivery_statistics: {}, financial_operational_metrics: {}, audit_event_metrics: {},
  performance_latency_reporting: {}, error_rate_reporting: {}, feature_flags: {}, operational_alerts_scaffold: {},
  export_scaffold: {}, guardrails: [],
};

function MetricCard({ label, value, detail }) {
  return <div className="mutual-aid-metric-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function BarList({ title, data = {} }) {
  const entries = Object.entries(data || {});
  const max = Math.max(1, ...entries.map(([, value]) => Number(value) || 0));
  return <article className="mutual-aid-card"><h2>{title}</h2><div className="mutual-aid-analytics-bars">{entries.map(([label, value]) => <div key={label}><span>{label.replaceAll("_", " ")}</span><strong>{value}</strong><progress value={value} max={max}>{value}</progress></div>)}</div></article>;
}

function previewExport() {
  window.alert("Operations report export scaffold preview only: no file is generated, stored, scheduled, or delivered.");
}

export default function MutualAidOperationsDashboard() {
  const [state, setState] = useState({ loading: true, error: "", data: emptyOps });
  useEffect(() => {
    api("/mutual-aid/admin/operations/dashboard", { method: "GET" })
      .then((data) => setState({ loading: false, error: "", data }))
      .catch((err) => setState({ loading: false, error: err.message || "Unable to load Mutual Aid operations metrics.", data: emptyOps }));
  }, []);
  const data = state.data || emptyOps;
  const requestLifecycle = data.request_lifecycle || {};
  const financial = data.financial_operational_metrics || {};
  const alerts = data.operational_alerts_scaffold?.alerts || [];

  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--operations">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-operations-title">
        <p className="mutual-aid-kicker">Admin Only · Read-Only Observability</p>
        <h1 id="mutual-aid-operations-title">Mutual Aid Observability & Operations Dashboard</h1>
        <p className="mutual-aid-subtitle">Operational metrics for request lifecycles, reviews, decisions, appeals, notifications, tracking records, audit activity, latency, errors, feature flags, and health. No external monitoring, alert delivery, payment processors, payouts, wallets, reimbursements, STAR, Black Dollars, ownership, or banking integrations.</p>
        <div className="mutual-aid-report-actions"><button onClick={() => window.print()}>Print operations view</button><button onClick={previewExport}>Preview export scaffold</button></div>
      </section>

      {state.loading ? <p className="mutual-aid-warning">Loading operations metrics…</p> : null}
      {state.error ? <p className="mutual-aid-warning">{state.error}</p> : null}

      <section className="mutual-aid-dashboard-grid" aria-label="Mutual Aid read-only operations metrics">
        <article className="mutual-aid-card mutual-aid-card--wide"><h2>System Health</h2><div className="mutual-aid-executive-grid"><MetricCard label="Health" value={data.health?.status || "unknown"} detail="Backend health endpoint status" /><MetricCard label="Feature Flag" value={String(data.feature_enabled || false)} detail="MUTUAL_AID_OBSERVABILITY_ENABLED" /><MetricCard label="Requests" value={requestLifecycle.total_requests || 0} detail="Lifecycle records" /><MetricCard label="Tracking Records" value={financial.disbursement_tracking_records || 0} detail="Disbursement records only; no execution" /></div></article>
        <BarList title="Request Lifecycle by Status" data={requestLifecycle.by_status} />
        <BarList title="Requests by Category" data={requestLifecycle.by_category} />
        <BarList title="Notifications by Delivery Status" data={data.notification_delivery_statistics?.by_delivery_status} />
        <BarList title="Audit Events by Action" data={data.audit_event_metrics?.by_action} />
        <article className="mutual-aid-card"><h2>Latency Reporting</h2><p>Review average: <strong>{data.performance_latency_reporting?.request_review_latency?.average_hours || 0} hours</strong></p><p>Decision p95: <strong>{data.performance_latency_reporting?.request_decision_latency?.p95_hours || 0} hours</strong></p><p>Appeal average: <strong>{data.performance_latency_reporting?.appeal_processing_latency?.average_hours || 0} hours</strong></p></article>
        <article className="mutual-aid-card"><h2>Error Rate Reporting</h2><p>Request error rate: <strong>{data.error_rate_reporting?.request_error_rate || 0}%</strong></p><p>Notification error records: <strong>{data.error_rate_reporting?.notification_error_records || 0}</strong></p><p>Route guardrail violations: <strong>{data.error_rate_reporting?.route_guardrail_violations || 0}</strong></p></article>
        <article className="mutual-aid-card mutual-aid-card--wide"><h2>Operational Alerts Scaffold</h2>{alerts.map((alert) => <p key={alert.key}><strong>{alert.status}</strong>: {alert.message}</p>)}<p>No email, SMS, Slack, PagerDuty, webhook, or external alert integration is configured.</p></article>
        <article className="mutual-aid-card mutual-aid-card--wide"><h2>Feature Flag Status</h2><div className="mutual-aid-notice-grid">{Object.entries(data.feature_flags || {}).map(([key, value]) => <strong key={key}>{key}: {String(value)}</strong>)}</div></article>
      </section>
    </main>
  );
}
