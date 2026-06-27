import { useEffect, useState } from "react";
import { getMutualAidComplianceChecklist, getMutualAidRbacAudit, getMutualAidSecurityHealth } from "../api/mutualAidRequests";

export default function MutualAidSecurityDashboard() {
  const [state, setState] = useState({ loading: true, error: "", health: null, rbac: null, compliance: null });

  useEffect(() => {
    Promise.all([getMutualAidSecurityHealth(), getMutualAidRbacAudit(), getMutualAidComplianceChecklist()])
      .then(([health, rbac, compliance]) => setState({ loading: false, error: "", health, rbac, compliance }))
      .catch((err) => setState({ loading: false, error: err.message || "Security dashboard unavailable", health: null, rbac: null, compliance: null }));
  }, []);

  if (state.loading) return <main className="mutual-aid-page"><p>Loading Mutual Aid security dashboard…</p></main>;
  if (state.error) return <main className="mutual-aid-page"><h1>Security dashboard unavailable</h1><p>{state.error}</p></main>;

  const checks = state.health?.checks || [];
  const compliance = state.compliance?.checklist || [];
  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--security">
      <section className="mutual-aid-hero cosmic-readable-shell">
        <p className="mutual-aid-kicker">Admin Only · Security & Compliance</p>
        <h1>Mutual Aid Security Dashboard</h1>
        <p className="mutual-aid-subtitle">Read-only hardening report for headers, RBAC, audit integrity, PII masking, retention scaffolds, and forbidden integration guardrails.</p>
      </section>
      <section className="mutual-aid-grid">
        <article className="mutual-aid-card"><h2>Security health</h2>{checks.map((check) => <p key={check.key}>{check.passed ? "✅" : "❌"} {check.label}</p>)}</article>
        <article className="mutual-aid-card"><h2>Compliance checklist</h2>{compliance.map((check) => <p key={check.key}>{check.passed ? "✅" : "❌"} {check.label}</p>)}</article>
        <article className="mutual-aid-card mutual-aid-card--wide"><h2>RBAC audit</h2><pre>{JSON.stringify(state.rbac?.roles || {}, null, 2)}</pre></article>
      </section>
    </main>
  );
}
