import { useEffect, useState } from "react";
import { getMutualAidPilotSmokeTests } from "../api/mutualAidRequests";

function CheckList({ items = [] }) {
  return items.map((item) => (
    <li key={item.key || item.label} className={item.passed ? "is-pass" : "is-blocked"}>
      <strong>{item.passed ? "PASS" : "FAIL"}: {item.label}</strong> — {item.detail}
    </li>
  ));
}

export default function MutualAidPilotSmokeTestsPage() {
  const [state, setState] = useState({ loading: true, error: "", data: null });

  useEffect(() => {
    let active = true;
    getMutualAidPilotSmokeTests()
      .then((data) => active && setState({ loading: false, error: "", data }))
      .catch((error) => active && setState({ loading: false, error: error?.message || "Unable to load pilot smoke tests.", data: null }));
    return () => { active = false; };
  }, []);

  if (state.loading) return <main className="mutual-aid-page"><p>Loading Mutual Aid pilot smoke tests…</p></main>;
  if (state.error) return <main className="mutual-aid-page"><h1>Pilot smoke tests unavailable</h1><p>{state.error}</p></main>;

  const data = state.data || {};

  return (
    <main className="mutual-aid-page mutual-aid-page--admin">
      <section className="mutual-aid-hero">
        <p className="eyebrow">Admin-only · Phase 11 · Read-only smoke test</p>
        <h1>Mutual Aid pilot operations smoke tests</h1>
        <p>{data.no_persistence_warning}</p>
      </section>

      <section className="mutual-aid-grid">
        <article className="mutual-aid-card"><h2>Status</h2><p><strong>{data.status?.toUpperCase()}</strong></p></article>
        <article className="mutual-aid-card"><h2>Fund status</h2><p>{data.fund_status}</p></article>
        <article className="mutual-aid-card"><h2>Activation threshold</h2><p>{data.activation_threshold}</p></article>
        <article className="mutual-aid-card"><h2>Read only</h2><p>{data.read_only ? "Yes — no writes" : "No"}</p></article>
      </section>

      <section className="mutual-aid-card"><h2>Blockers</h2>{data.blockers?.length ? <ul><CheckList items={data.blockers} /></ul> : <p>No blockers reported.</p>}</section>
      <section className="mutual-aid-card"><h2>Next action</h2><p>{data.next_action}</p></section>
      <section className="mutual-aid-card"><h2>Smoke test checks</h2><ul><CheckList items={data.checks} /></ul></section>
      <section className="mutual-aid-card"><h2>Pilot-safe warnings</h2><ul>{data.pilot_safe_warnings?.map((warning) => <li key={warning}>{warning}</li>)}</ul></section>
      <section className="mutual-aid-card"><h2>No persistence warning</h2><p>{data.no_persistence_warning}</p></section>
    </main>
  );
}
