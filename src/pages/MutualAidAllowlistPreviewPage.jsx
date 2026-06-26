import React from "react";
import { Link } from "react-router-dom";
import {
  ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL,
  MUTUAL_AID_ACTIVATION_THRESHOLD,
  MUTUAL_AID_STATUS,
} from "../config";
import { formatMutualAidCurrency } from "../mutualAidFundProgress";
import "../styles/mutualAid.css";

const pilotGroupGuidance = [
  "5 to 10 trusted internal members",
  "2 to 3 admins",
  "3 to 5 committee reviewers",
  "1 treasurer or finance role",
  "1 governance approver",
];

const eligibilityPreview = [
  "Active member",
  "Verified profile",
  "Good standing",
  "Accepted mutual aid policy",
  "No active fraud/suspension flag",
  "Inside pilot allowlist",
];

const exampleRows = [
  {
    name: "Example Member A",
    role: "Internal member",
    eligibility: "Would require verification",
    status: "Example only",
  },
  {
    name: "Example Reviewer B",
    role: "Committee reviewer",
    eligibility: "Would require policy acceptance",
    status: "Example only",
  },
  {
    name: "Example Admin C",
    role: "Admin",
    eligibility: "Would require governance confirmation",
    status: "Example only",
  },
];

const referenceDocs = [
  "SIMBA_MUTUAL_AID_DOCS_INDEX",
  "SOCIETY_BINDER",
  "OPERATING_APPENDIX",
  "TECHNICAL_SPEC",
  "LANGUAGE_PACK",
  "PILOT_LAUNCH_PLAN",
];

export default function MutualAidAllowlistPreviewPage() {
  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--allowlist">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-allowlist-title">
        <p className="mutual-aid-kicker">Admin Only · Allowlist Pilot Access Shell</p>
        <h1 id="mutual-aid-allowlist-title">Mutual Aid Allowlist Pilot Access Preview</h1>
        <p className="mutual-aid-subtitle">
          Static planning page for how future allowlisted Mutual Aid pilot access may be prepared after approval.
        </p>
        <div className="mutual-aid-status mutual-aid-status--warning" aria-label="Current allowlist status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>Status: Preview Only / Not Active</span>
        </div>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell" aria-label="Allowlist preview warnings">
        <strong>No access is granted from this page.</strong> Requests are not open yet, and Mutual Aid distributions are not allowed before activation.
        <br />
        <strong>Static shell only:</strong> This page does not save people, change permissions, open reviews, process approvals, or move funds.
      </section>

      <nav className="mutual-aid-preview-nav" aria-label="Mutual Aid admin planning links">
        <Link to="/admin/mutual-aid">Admin planning</Link>
        {ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL ? <Link to="/admin/mutual-aid/pilot-readiness">Pilot readiness</Link> : null}
        <Link to="/mutual-aid">Public overview</Link>
      </nav>

      <section className="mutual-aid-grid" aria-label="Allowlist pilot access planning cards">
        <article className="mutual-aid-card">
          <h2>Building Toward Activation</h2>
          <p>
            Mutual Aid remains in preparation. Future pilot access must wait for the approved governance, operations, technical, and launch controls.
          </p>
          <div className="mutual-aid-status mutual-aid-status--compact">
            <span className="mutual-aid-status__dot" aria-hidden="true" />
            <span>{MUTUAL_AID_STATUS}</span>
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Activation threshold</h2>
          <p className="mutual-aid-threshold__amount">{formatMutualAidCurrency(MUTUAL_AID_ACTIVATION_THRESHOLD)}</p>
          <p>Preview-only threshold display. No distributions are allowed before activation.</p>
        </article>

        <article className="mutual-aid-card">
          <h2>Future pilot group guidance</h2>
          <ul className="mutual-aid-list">
            {pilotGroupGuidance.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>

        <article className="mutual-aid-card">
          <h2>Future eligibility preview</h2>
          <ul className="mutual-aid-list">
            {eligibilityPreview.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <div className="mutual-aid-card__header">
            <div>
              <h2>Example allowlist table</h2>
              <p>Fake rows for planning conversation only. Buttons are disabled and no information is stored.</p>
            </div>
            <button className="mutual-aid-disabled-button" type="button" disabled>Add to allowlist</button>
          </div>

          <div className="mutual-aid-table mutual-aid-table--allowlist" aria-label="Disabled example allowlist rows">
            <div className="mutual-aid-table__row mutual-aid-table__row--header">
              <strong>Name</strong>
              <strong>Pilot role</strong>
              <strong>Eligibility note</strong>
              <strong>Status</strong>
              <strong>Action</strong>
            </div>
            {exampleRows.map((row) => (
              <div className="mutual-aid-table__row" key={row.name} aria-disabled="true">
                <span>{row.name}</span>
                <span>{row.role}</span>
                <span>{row.eligibility}</span>
                <span className="mutual-aid-example-badge">{row.status}</span>
                <button type="button" disabled>Remove</button>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Approved document sources</h2>
          <div className="mutual-aid-badges" aria-label="Approved document set">
            {referenceDocs.map((doc) => <span key={doc}>{doc}</span>)}
          </div>
          <p className="mutual-aid-note">Source labels identify the approved Mutual Aid bundle used for this static allowlist shell.</p>
        </article>
      </section>
    </main>
  );
}
