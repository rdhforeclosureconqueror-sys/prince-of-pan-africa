import React, { useEffect, useState } from "react";
import { getMutualAidCompletionDashboard, getMutualAidDocumentationIndex } from "../api/mutualAidRequests";
import "../styles/mutualAid.css";

export default function MutualAidDocumentationDashboard() {
  const [state, setState] = useState({ loading: true, docs: null, dashboard: null, error: "" });

  useEffect(() => {
    let cancelled = false;
    Promise.all([getMutualAidDocumentationIndex(), getMutualAidCompletionDashboard()])
      .then(([docs, dashboard]) => {
        if (!cancelled) setState({ loading: false, docs, dashboard, error: "" });
      })
      .catch((error) => {
        if (!cancelled) setState({ loading: false, docs: null, dashboard: null, error: error.message || "Unable to load Mutual Aid documentation." });
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <main className="mutual-aid-page mutual-aid-page--admin">
      <section className="mutual-aid-hero cosmic-readable-shell">
        <p className="mutual-aid-kicker">Admin Only · Phase 15</p>
        <h1>Mutual Aid Documentation & Pilot Completion</h1>
        <p className="mutual-aid-subtitle">Read-only in-application documentation, training, checklists, catalogs, and final completion status.</p>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell">
        <strong>Read-only:</strong> This dashboard has no write actions, no payment connection, no payout execution, no wallet balances, and no external documentation portal.
      </section>

      {state.loading ? <p className="mutual-aid-note">Loading completion dashboard...</p> : null}
      {state.error ? <p className="mutual-aid-note">{state.error}</p> : null}

      {state.dashboard ? (
        <section className="mutual-aid-grid">
          <article className="mutual-aid-card">
            <h2>Final readiness</h2>
            <p><strong>Status:</strong> {state.dashboard.status}</p>
            <p><strong>Read only:</strong> {state.dashboard.read_only ? "Yes" : "No"}</p>
            <p><strong>Mutations enabled:</strong> {state.dashboard.dashboard?.mutations_enabled ? "Yes" : "No"}</p>
          </article>
          <article className="mutual-aid-card mutual-aid-card--wide">
            <h2>Checks</h2>
            <ul className="mutual-aid-list">
              {state.dashboard.checks.map((check) => <li key={check.key}><strong>{check.passed ? "Pass" : "Needs attention"}: {check.label}</strong> — {check.detail}</li>)}
            </ul>
          </article>
          <article className="mutual-aid-card mutual-aid-card--wide">
            <h2>Available documents</h2>
            <div className="mutual-aid-badges">
              {(state.docs?.documents || []).map((doc) => <span key={doc.slug}>{doc.title}</span>)}
            </div>
          </article>
        </section>
      ) : null}
    </main>
  );
}
