import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import "../styles/mutualAid.css";

const emptyAnalytics = {
  totals: {}, timing: {}, volume: { by_category: {}, by_urgency: {}, by_status: {} }, rates: {},
  notifications: {}, audit_activity: {}, disbursements: {}, budgets: {}, activation: {}, executive_kpis: [], reporting: {}, guardrails: [],
};

function BarList({ title, data = {} }) {
  const max = Math.max(1, ...Object.values(data));
  return <article className="mutual-aid-card"><h2>{title}</h2><div className="mutual-aid-analytics-bars">{Object.entries(data).map(([label, value]) => <div key={label}><span>{label.replaceAll("_", " ")}</span><strong>{value}</strong><progress value={value} max={max}>{value}</progress></div>)}</div></article>;
}

function scaffoldExport(kind) {
  window.alert(`${kind} export scaffold only: no files are generated, stored, persisted, or scheduled.`);
}

export default function MutualAidExecutiveAnalyticsPage() {
  const [state, setState] = useState({ loading: true, error: "", data: emptyAnalytics });
  useEffect(() => {
    api("/mutual-aid/admin/analytics/executive", { method: "GET" })
      .then((data) => setState({ loading: false, error: "", data }))
      .catch((err) => setState({ loading: false, error: err.message || "Unable to load Mutual Aid analytics.", data: emptyAnalytics }));
  }, []);
  const data = state.data || emptyAnalytics;
  const executiveSummary = useMemo(() => {
    const t = data.totals || {}; const a = data.activation || {};
    return `Read-only executive analytics summarize ${t.total_requests || 0} requests, ${t.approved || 0} approved, ${t.partially_approved || 0} partially approved, ${t.denied || 0} denied, and ${t.appealed || 0} appealed. Activation remains ${a.status || "Building Toward Activation"} at ${a.progress_percent || 0}%.`;
  }, [data]);

  return <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--analytics">
    <section className="mutual-aid-hero cosmic-readable-shell"><p className="mutual-aid-kicker">Admin · Governance · Treasurer · Read Only</p><h1>Mutual Aid Executive Analytics & Reporting</h1><p className="mutual-aid-subtitle">Executive KPI cards, trend-style breakdowns, budget utilization, activation progress, and printable reporting. No payment processors, money movement, payout execution, wallet balances, reimbursement logic, persistence, file storage, or scheduled reports.</p><div className="mutual-aid-report-actions"><button onClick={() => window.print()}>Print executive report</button><button onClick={() => scaffoldExport("CSV")}>CSV scaffold</button><button onClick={() => scaffoldExport("PDF")}>PDF scaffold</button></div></section>
    {state.loading ? <p className="mutual-aid-warning">Loading executive analytics…</p> : null}
    {state.error ? <p className="mutual-aid-warning">{state.error}</p> : null}
    <section className="mutual-aid-grid">
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Executive KPI Summary</h2><div className="mutual-aid-executive-kpi-grid">{(data.executive_kpis || []).map((kpi) => <div className="mutual-aid-executive-summary-card" key={kpi.label}><span>{kpi.label}</span><strong>{kpi.value}</strong><small>{kpi.detail}</small></div>)}</div></article>
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Executive Summary</h2><p>{executiveSummary}</p></article>
      <BarList title="Request Volume by Category" data={data.volume?.by_category} /><BarList title="Request Volume by Urgency" data={data.volume?.by_urgency} /><BarList title="Status Breakdown" data={data.volume?.by_status} /><BarList title="Disbursement Tracking by Status" data={data.disbursements?.by_status} />
      <article className="mutual-aid-card"><h2>Timing & Rates</h2><p>Average review time: <strong>{data.timing?.average_review_time_hours || 0} hours</strong></p><p>Average decision time: <strong>{data.timing?.average_decision_time_hours || 0} hours</strong></p><p>Approval rate: <strong>{data.rates?.approval_rate || 0}%</strong></p><p>Appeal rate: <strong>{data.rates?.appeal_rate || 0}%</strong></p></article>
      <article className="mutual-aid-card"><h2>Activation Progress</h2><p>{data.activation?.status}</p><progress value={data.activation?.progress_percent || 0} max="100">{data.activation?.progress_percent || 0}%</progress><p><strong>{data.activation?.current_progress || 0}</strong> / {data.activation?.activation_threshold || 20000}</p></article>
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Category Budget Utilization</h2><div className="mutual-aid-analytics-bars">{(data.budgets?.category_budget_utilization || []).map((b) => <div key={b.category}><span>{b.category}</span><strong>{b.utilization_rate}%</strong><progress value={b.utilization_rate} max="100">{b.utilization_rate}%</progress><small>{b.tracked_amount + b.reserved_amount} / {b.budget_amount} {b.currency}</small></div>)}</div></article>
      <article className="mutual-aid-card"><h2>Notification Totals</h2><p>Total recorded-only notifications: <strong>{data.notifications?.total || 0}</strong></p></article><article className="mutual-aid-card"><h2>Audit Activity Totals</h2><p>Total audit events: <strong>{data.audit_activity?.total || 0}</strong></p></article>
    </section>
  </main>;
}
