import { useEffect, useState } from "react";
import { getMutualAidPilotLaunchLock } from "../api/mutualAidRequests";

export default function MutualAidPilotLaunchLockPage() {
  const [state, setState] = useState({ loading: true, error: "", data: null });

  useEffect(() => {
    let active = true;
    getMutualAidPilotLaunchLock()
      .then((data) => active && setState({ loading: false, error: "", data }))
      .catch((error) => active && setState({ loading: false, error: error?.message || "Unable to load pilot launch lock.", data: null }));
    return () => { active = false; };
  }, []);

  if (state.loading) return <main className="mutual-aid-page"><p>Loading Mutual Aid pilot launch lock…</p></main>;
  if (state.error) return <main className="mutual-aid-page"><h1>Pilot launch lock unavailable</h1><p>{state.error}</p></main>;

  const data = state.data || {};
  const checks = data.checks || [];
  const blockers = data.blockers || [];

  return (
    <main className="mutual-aid-page">
      <section className="mutual-aid-hero">
        <p className="eyebrow">Admin-only pilot safety verification</p>
        <h1>Mutual Aid Phase 9 pilot launch lock</h1>
        <p>This operator QA screen is read-only. Checklist controls are disabled and no signoff, payment, payout, wallet, or persistence action is performed here.</p>
      </section>

      <section className="mutual-aid-grid">
        <article className="mutual-aid-card">
          <h2>Go / no-go status</h2>
          <p><strong>{data.status === "go" ? "GO" : "NO-GO"}</strong></p>
          <p>{data.ready ? "Pilot-safe conditions are currently verified." : "Blockers must be cleared before pilot launch."}</p>
        </article>
        <article className="mutual-aid-card">
          <h2>Next required action</h2>
          <p>{data.next_required_action}</p>
        </article>
      </section>

      <section className="mutual-aid-card" aria-label="Operator QA checklist">
        <h2>Disabled operator QA checklist</h2>
        {checks.map((check) => (
          <label key={check.key} className="mutual-aid-check-row">
            <input type="checkbox" checked={Boolean(check.passed)} disabled readOnly />
            <span><strong>{check.label}</strong><br />{check.detail}</span>
          </label>
        ))}
      </section>

      <section className="mutual-aid-card">
        <h2>Blockers</h2>
        {blockers.length ? blockers.map((blocker) => <p key={blocker.key}><strong>{blocker.label}:</strong> {blocker.detail}</p>) : <p>No blockers reported by the read-only backend verification.</p>}
      </section>
    </main>
  );
}
