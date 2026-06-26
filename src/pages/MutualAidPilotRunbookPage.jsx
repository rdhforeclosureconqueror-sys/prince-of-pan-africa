import { useEffect, useState } from "react";
import { getMutualAidPilotRunbook } from "../api/mutualAidRequests";

function CheckList({ items = [] }) {
  return items.map((item) => (
    <li key={item.key || item.label} className={item.passed ? "is-pass" : "is-blocked"}>
      <strong>{item.label}</strong> — {item.detail}
    </li>
  ));
}

export default function MutualAidPilotRunbookPage() {
  const [state, setState] = useState({ loading: true, error: "", data: null });

  useEffect(() => {
    let active = true;
    getMutualAidPilotRunbook()
      .then((data) => active && setState({ loading: false, error: "", data }))
      .catch((error) => active && setState({ loading: false, error: error?.message || "Unable to load pilot runbook.", data: null }));
    return () => { active = false; };
  }, []);

  if (state.loading) return <main className="mutual-aid-page"><p>Loading Mutual Aid pilot runbook…</p></main>;
  if (state.error) return <main className="mutual-aid-page"><h1>Pilot runbook unavailable</h1><p>{state.error}</p></main>;

  const data = state.data || {};

  return (
    <main className="mutual-aid-page mutual-aid-runbook-print">
      <section className="mutual-aid-hero">
        <p className="eyebrow">Admin-only · Phase 10 · Export-ready</p>
        <h1>Mutual Aid pilot runbook and go/no-go export</h1>
        <p>This print-friendly view is read-only. It does not download files, store exports, persist signoff, move money, execute payouts, or expose wallet balances.</p>
      </section>

      <section className="mutual-aid-grid">
        <article className="mutual-aid-card"><h2>Go / no-go result</h2><p><strong>{data.go_no_go_result}</strong></p></article>
        <article className="mutual-aid-card"><h2>Pilot status</h2><p>{data.pilot_status}</p></article>
        <article className="mutual-aid-card"><h2>Phase 8 readiness</h2><p>{data.phase8_readiness?.status}</p></article>
        <article className="mutual-aid-card"><h2>Phase 9 launch lock</h2><p>{data.phase9_launch_lock?.status}</p></article>
      </section>

      <section className="mutual-aid-card"><h2>Blockers</h2>{data.blockers?.length ? <ul><CheckList items={data.blockers} /></ul> : <p>No blockers reported.</p>}</section>
      <section className="mutual-aid-card"><h2>Operator checklist</h2><ul><CheckList items={data.operator_checklist} /></ul></section>
      <section className="mutual-aid-card"><h2>Required roles</h2><ul>{data.required_roles?.map((role) => <li key={role}>{role}</li>)}</ul></section>
      <section className="mutual-aid-card"><h2>Required flags</h2><ul>{data.required_flags?.map((flag) => <li key={flag}><code>{flag}</code></li>)}</ul></section>
      <section className="mutual-aid-card"><h2>Required docs / policies</h2><ul>{data.required_docs_policies?.map((doc) => <li key={doc}>{doc}</li>)}</ul></section>
      <section className="mutual-aid-card"><h2>Read-only guardrails</h2><ul>{data.guardrails?.map((guardrail) => <li key={guardrail}>{guardrail}</li>)}</ul></section>
    </main>
  );
}
