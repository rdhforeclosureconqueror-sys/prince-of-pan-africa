import React from "react";
import { Link } from "react-router-dom";
import "../styles/mutualAid.css";

const activationRequirements = [
  "Approved policy",
  "Governance process",
  "Accounting controls",
  "Privacy rules",
  "Approval controls",
  "Trained committee",
  "Legal/tax/compliance review before public launch",
];

const pilotReadinessChecklist = [
  "Binder approved",
  "Operating appendix approved",
  "Technical spec approved",
  "Language pack approved",
  "Pilot launch plan approved",
  "Professional review scheduled or completed",
  "Committee appointed",
  "Committee trained",
  "Conflict-of-interest policy accepted",
  "Privacy policy reviewed",
  "Feature flags configured in a future approved phase",
  "Allowlist configured in a future approved phase",
  "Admin permissions tested",
  "Reviewer permissions tested",
  "Treasurer permissions tested",
  "Test request completed",
  "Audit logs verified",
  "Safe language reviewed",
  "Stop conditions accepted",
];

const stopConditions = [
  "Private hardship details are exposed",
  "Money is moved without authorization",
  "Reviewers approve conflicted cases",
  "Members are promised support without review",
  "Fund records do not reconcile",
  "Fraud patterns appear",
  "Committee cannot explain decisions",
  "Professional review concern is raised",
  "Platform permissions fail",
  "Members can see other members' requests",
];

export default function MutualAidAdminPlanningPage() {
  return (
    <main className="mutual-aid-page mutual-aid-page--admin">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-admin-title">
        <p className="mutual-aid-kicker">Internal Admin Planning</p>
        <h1 id="mutual-aid-admin-title">Mutual Aid Society Readiness</h1>
        <p className="mutual-aid-subtitle">
          Phase 3 planning scaffold for activation requirements, pilot readiness, and go/no-go safeguards.
        </p>
        <div className="mutual-aid-status" aria-label="Current status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>Building Toward Activation</span>
        </div>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell" aria-label="Planning-only warnings">
        <strong>Planning-only:</strong> This internal page does not create live request, review, ledger,
        contribution, payout, wallet, or payment functionality.
        <br />
        <strong>No distributions:</strong> No mutual aid distributions are allowed before activation.
      </section>

      <section className="mutual-aid-grid" aria-label="Mutual Aid admin readiness plan">
        <article className="mutual-aid-card mutual-aid-threshold">
          <h2>Activation threshold</h2>
          <p className="mutual-aid-threshold__amount">$20,000</p>
          <p>
            Activation requires the designated Mutual Aid / Community Development Fund to reach this amount in
            available or committed funding and all governance controls to be approved.
          </p>
        </article>

        <article className="mutual-aid-card">
          <h2>Activation requirements</h2>
          <ul className="mutual-aid-list mutual-aid-checklist">
            {activationRequirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Pilot readiness checklist</h2>
          <div className="mutual-aid-checklist-grid">
            {pilotReadinessChecklist.map((item) => (
              <label className="mutual-aid-check" key={item}>
                <input type="checkbox" disabled />
                <span>{item}</span>
              </label>
            ))}
          </div>
          <p className="mutual-aid-note">
            Disabled checklist controls are visual planning markers only and do not persist or submit data.
          </p>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Stop conditions</h2>
          <p>Pause pilot planning immediately if any of these conditions appear:</p>
          <ul className="mutual-aid-list mutual-aid-list--danger">
            {stopConditions.map((condition) => (
              <li key={condition}>{condition}</li>
            ))}
          </ul>
        </article>

        <article className="mutual-aid-card">
          <h2>Next planned phase</h2>
          <p>
            Phase 4 is a future, separately approved internal pilot workflow test with manual controls only after
            governance, privacy, professional review, and permission safeguards are ready.
          </p>
        </article>

        <article className="mutual-aid-card">
          <h2>Public overview</h2>
          <p>
            The public display-only overview may remain available separately when enabled. This admin page is for
            internal readiness planning.
          </p>
          <Link className="mutual-aid-link-button" to="/mutual-aid">View /mutual-aid overview</Link>
        </article>
      </section>
    </main>
  );
}
