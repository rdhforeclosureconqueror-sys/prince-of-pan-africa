import { useEffect, useState } from "react";
import { getMutualAidDisbursements, getMutualAidFinancialControls } from "../api/mutualAidRequests";
import { formatMutualAidCurrency } from "../mutualAidFundProgress";

export default function MutualAidFinancialControlsPage() {
  const [state, setState] = useState({ loading: true, error: "", controls: null, disbursements: [] });

  useEffect(() => {
    let active = true;
    Promise.all([getMutualAidFinancialControls(), getMutualAidDisbursements()])
      .then(([controls, disbursements]) => {
        if (!active) return;
        setState({ loading: false, error: "", controls, disbursements: disbursements?.disbursements || [] });
      })
      .catch((error) => {
        if (!active) return;
        setState({ loading: false, error: error?.message || "Unable to load financial controls.", controls: null, disbursements: [] });
      });
    return () => { active = false; };
  }, []);

  if (state.loading) return <main className="mutual-aid-page"><p>Loading Mutual Aid financial controls…</p></main>;
  if (state.error) return <main className="mutual-aid-page"><h1>Financial controls unavailable</h1><p>{state.error}</p></main>;

  const balance = state.controls?.balance || {};
  const budgets = state.controls?.category_budgets || [];
  const reports = state.controls?.reconciliation_reports || [];

  return (
    <main className="mutual-aid-page">
      <section className="mutual-aid-hero">
        <p className="eyebrow">Treasurer / Admin only</p>
        <h1>Mutual Aid financial controls</h1>
        <p>Administrative planning for fund balance, reserve rules, category budgets, disbursement tracking, receipts, reconciliation, audit, and status history. This screen does not connect payment processors or move money.</p>
      </section>

      <section className="mutual-aid-grid">
        <article className="mutual-aid-card"><h2>Fund balance read model</h2><p>{formatMutualAidCurrency(balance.current_balance || 0)} current</p><p>{formatMutualAidCurrency(balance.available_for_disbursement || 0)} available after {balance.reserve_percent || 0}% reserve</p></article>
        <article className="mutual-aid-card"><h2>Approval threshold</h2><p>{formatMutualAidCurrency(balance.approval_threshold || 0)}</p><p>Amounts above this threshold require admin review.</p></article>
      </section>

      <section className="mutual-aid-card"><h2>Category budgets</h2>{budgets.length ? budgets.map((b) => <p key={b.id}>{b.category}: {formatMutualAidCurrency(b.budget_amount)} budget / {formatMutualAidCurrency(b.reserved_amount)} reserved</p>) : <p>No category budgets have been configured yet.</p>}</section>
      <section className="mutual-aid-card"><h2>Disbursement tracking</h2>{state.disbursements.length ? state.disbursements.map((d) => <p key={d.id}>Request #{d.request_id}: {formatMutualAidCurrency(d.amount)} — {d.status}{d.receipt_required ? " — receipt required" : ""}</p>) : <p>No administrative disbursement records yet.</p>}</section>
      <section className="mutual-aid-card"><h2>Reconciliation report scaffold</h2>{reports.length ? reports.map((r) => <p key={r.id}>Report #{r.id}: {r.status}</p>) : <p>No reconciliation reports have been drafted yet.</p>}</section>
    </main>
  );
}
