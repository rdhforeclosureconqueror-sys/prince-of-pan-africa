import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { ENABLE_MUTUAL_AID_PILOT_HARDENING } from "../config";
import { formatMutualAidCurrency, MUTUAL_AID_ACTIVATION_THRESHOLD, MUTUAL_AID_STATUS } from "../mutualAidFundProgress";
import "../styles/mutualAid.css";

export const readinessStages = [
  "Documentation approved",
  "Policy approved",
  "Committee appointed",
  "Committee trained",
  "Conflict policy accepted",
  "Privacy review complete",
  "Accounting controls approved",
  "Legal/tax/compliance review complete",
  "Feature flags confirmed",
  "Allowlist prepared",
  "Audit logs verified",
  "Stop conditions accepted",
];

const goNoGoChecks = [
  { label: "Go", detail: "Only after every readiness stage is confirmed outside this display-only shell." },
  { label: "No-Go", detail: "Remain inactive if any governance, privacy, controls, training, or review item is incomplete." },
];

const stopConditions = [
  "Private hardship details are exposed outside the approved committee process.",
  "Controls cannot show who viewed or changed pilot readiness records.",
  "Conflicted committee participation is not paused and documented.",
  "Accounting controls are incomplete or cannot be reconciled.",
  "Professional legal, tax, or compliance concerns remain unresolved.",
  "Members are told distributions can occur before activation.",
];

const referenceDocs = [
  "SIMBA_MUTUAL_AID_DOCS_INDEX",
  "SOCIETY_BINDER",
  "OPERATING_APPENDIX",
  "TECHNICAL_SPEC",
  "LANGUAGE_PACK",
  "PILOT_LAUNCH_PLAN",
];

export default function MutualAidPilotReadinessPage() {
  const [verification, setVerification] = useState(null);
  const [verificationError, setVerificationError] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (!ENABLE_MUTUAL_AID_PILOT_HARDENING) return undefined;
    api("/mutual-aid/admin/pilot-readiness/verification")
      .then((data) => { if (!cancelled) setVerification(data); })
      .catch((error) => { if (!cancelled) setVerificationError(error.message || "Unable to load readiness verification."); });
    return () => { cancelled = true; };
  }, []);

  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--readiness">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-readiness-title">
        <p className="mutual-aid-kicker">Admin Only · Pilot Readiness Shell</p>
        <h1 id="mutual-aid-readiness-title">Mutual Aid Pilot Readiness Workflow</h1>
        <p className="mutual-aid-subtitle">
          Static board for the work that must be completed before live Mutual Aid pilot requests can be enabled.
        </p>
        <div className="mutual-aid-status" aria-label="Current status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>Status: {MUTUAL_AID_STATUS}</span>
        </div>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell" aria-label="Readiness-only warnings">
        <strong>No distributions before activation:</strong> Mutual Aid distributions are not allowed before activation.
        <br />
        <strong>This page does not approve anything:</strong> It is a disabled, example-only readiness shell with no saved state.
      </section>

      <nav className="mutual-aid-preview-nav" aria-label="Mutual Aid admin links">
        <Link to="/admin/mutual-aid">Admin planning</Link>
        <Link to="/mutual-aid">Public overview</Link>
        <Link to="/admin/mutual-aid/review-preview">Review preview</Link>
      </nav>

      <section className="mutual-aid-grid" aria-label="Pilot readiness workflow board">
        <article className="mutual-aid-card">
          <h2>Activation threshold</h2>
          <p className="mutual-aid-threshold__amount">{formatMutualAidCurrency(MUTUAL_AID_ACTIVATION_THRESHOLD)}</p>
          <p>
            Threshold display is informational only. Live requests remain inactive until the approved readiness process is complete.
          </p>
        </article>

        <article className="mutual-aid-card">
          <h2>Next phase</h2>
          <p>
            Allowlisted request intake pilot, not active yet. A later approved phase must add any live intake process.
          </p>
          <button className="mutual-aid-disabled-button" type="button" disabled>Intake not active</button>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Phase 8 readiness verification</h2>
          <p>
            Pilot hardening flag: <strong>{ENABLE_MUTUAL_AID_PILOT_HARDENING ? "enabled" : "disabled"}</strong>.
            This flag defaults off and gates the live admin verification call.
          </p>
          {!ENABLE_MUTUAL_AID_PILOT_HARDENING ? (
            <p className="mutual-aid-note">Enable VITE_ENABLE_MUTUAL_AID_PILOT_HARDENING to query the admin-only readiness endpoint.</p>
          ) : verificationError ? (
            <p className="mutual-aid-note">Verification unavailable: {verificationError}</p>
          ) : verification ? (
            <>
              <p><strong>Overall result:</strong> {verification.ready ? "Ready for controlled pilot verification" : "Not ready"}</p>
              <ul className="mutual-aid-list">
                {verification.checks.map((check) => (
                  <li key={check.key}>
                    <strong>{check.passed ? "Pass" : "Needs attention"}: {check.label}</strong> — {check.detail}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="mutual-aid-note">Loading readiness verification...</p>
          )}
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Pilot readiness stages</h2>
          <div className="mutual-aid-readiness-board">
            {readinessStages.map((stage, index) => (
              <label className="mutual-aid-readiness-stage" key={stage}>
                <input type="checkbox" disabled />
                <span className="mutual-aid-readiness-stage__number">{index + 1}</span>
                <span>{stage}</span>
                <em>Example marker only</em>
              </label>
            ))}
          </div>
          <p className="mutual-aid-note">Disabled checkboxes do not save, submit, or update readiness state.</p>
        </article>

        <article className="mutual-aid-card">
          <h2>Go / No-Go</h2>
          <div className="mutual-aid-go-no-go">
            {goNoGoChecks.map((item) => (
              <div key={item.label}>
                <strong>{item.label}</strong>
                <p>{item.detail}</p>
                <button className="mutual-aid-disabled-button" type="button" disabled>{item.label} decision disabled</button>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Stop conditions</h2>
          <ul className="mutual-aid-list mutual-aid-list--danger">
            {stopConditions.map((condition) => <li key={condition}>{condition}</li>)}
          </ul>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Approved document sources</h2>
          <div className="mutual-aid-badges" aria-label="Approved document set">
            {referenceDocs.map((doc) => <span key={doc}>{doc}</span>)}
          </div>
          <p className="mutual-aid-note">Source labels identify the approved Mutual Aid document bundle used for this static shell.</p>
        </article>
      </section>
    </main>
  );
}
