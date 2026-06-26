import React from "react";
import { Link } from "react-router-dom";
import "../styles/mutualAid.css";

const overviewCards = [
  { label: "Governance Status", value: "Planning", detail: "Static documentation center only" },
  { label: "Policies Complete", value: "9 of 12", detail: "Example planning count" },
  { label: "SOP Progress", value: "Draft", detail: "Example-only operating notes" },
  { label: "Legal Review", value: "Pending", detail: "No review occurs here" },
  { label: "Committee Status", value: "Not appointed", detail: "Example readiness marker" },
  { label: "Activation Readiness", value: "Not active", detail: "See pilot readiness page" },
];

const documents = [
  ["Mutual Aid Policy", "Draft", "Governance Lead", "May 12, 2026", "Aug 12, 2026"],
  ["Program Overview", "Ready for review", "Program Team", "May 18, 2026", "Aug 18, 2026"],
  ["Eligibility Policy", "Draft", "Policy Team", "May 20, 2026", "Aug 20, 2026"],
  ["Support Guidelines", "Draft", "Member Support", "May 22, 2026", "Aug 22, 2026"],
  ["Governance Charter", "In progress", "Governance Lead", "May 24, 2026", "Aug 24, 2026"],
  ["Committee Charter", "In progress", "Committee Sponsor", "May 26, 2026", "Aug 26, 2026"],
  ["Privacy Review", "Pending", "Privacy Reviewer", "May 28, 2026", "Aug 28, 2026"],
  ["Terms Review", "Pending", "Legal Reviewer", "May 30, 2026", "Aug 30, 2026"],
  ["FAQ", "Draft", "Communications", "Jun 2, 2026", "Sep 2, 2026"],
  ["Member Guide", "Draft", "Member Education", "Jun 4, 2026", "Sep 4, 2026"],
  ["Admin Guide", "Draft", "Operations", "Jun 6, 2026", "Sep 6, 2026"],
  ["Launch Checklist", "Not started", "Launch Team", "Jun 8, 2026", "Sep 8, 2026"],
];

const sopItems = ["Request Intake", "Review Process", "Distribution Planning", "Appeals Process", "Fraud Prevention", "Incident Response", "Member Communication", "Reporting"];
const complianceItems = ["Terms reviewed", "Privacy reviewed", "Legal reviewed", "Compliance reviewed", "Risk assessment completed"];
const resources = [
  ["Committee Handbook", "Example guide for committee expectations, meeting rhythm, and role boundaries."],
  ["Review Guide", "Static outline of future review considerations without workflow or approval behavior."],
  ["Ethics Expectations", "Planning notes for confidentiality, care, fairness, and stewardship."],
  ["Conflict of Interest Policy", "Example summary of disclosure expectations before activation."],
];
const decisions = [
  ["Apr 15, 2026", "Governance center scoped as preview-only documentation."],
  ["May 3, 2026", "Activation dependencies linked to pilot readiness planning."],
  ["May 21, 2026", "Committee resources marked as examples until formal approval."],
  ["Jun 10, 2026", "Future version management deferred to a later phase."],
];
const versions = [
  ["Mutual Aid Policy", "0.3", "Jun 1, 2026", "Draft"],
  ["Governance Charter", "0.2", "Jun 5, 2026", "In progress"],
  ["Privacy Review", "0.1", "Jun 8, 2026", "Pending"],
  ["Launch Checklist", "0.1", "Jun 12, 2026", "Not started"],
];
const reviews = [
  ["Quarterly Review", "Jul 15, 2026", "Example recurring governance review"],
  ["Annual Policy Review", "Jan 20, 2027", "Example annual policy checkpoint"],
  ["Committee Review", "Aug 5, 2026", "Example committee preparedness check"],
  ["Launch Readiness Review", "Sep 12, 2026", "Example pre-activation dependency review"],
];
const dependencies = [
  "Pilot readiness stages must be completed and confirmed outside this static center.",
  "Policies, privacy, legal, and compliance reviews must be complete before activation.",
  "Committee appointment, training, and conflict expectations must be resolved before launch.",
  "Accounting controls, audit expectations, and stop conditions must be approved before activation.",
];
const notices = ["Preview Only", "Not Active", "Planning Documentation", "No documents are stored", "No approvals occur here", "No uploads are available", "No workflow automation is implemented"];

function GovernanceBadge({ children }) {
  return <span className="mutual-aid-governance-badge">{children}</span>;
}

export default function MutualAidGovernanceCenter() {
  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--governance">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="governance-title">
        <p className="mutual-aid-kicker">Admin Only · Planning Documentation</p>
        <h1 id="governance-title">Mutual Aid Governance & Documentation Center</h1>
        <p className="mutual-aid-subtitle">Static example hub for organizing documents required before Mutual Aid activation. No live workflow, storage, uploads, approvals, or automation is implemented.</p>
        <div className="mutual-aid-badges" aria-label="Governance notices">{notices.map((notice) => <GovernanceBadge key={notice}>{notice}</GovernanceBadge>)}</div>
      </section>

      <nav className="mutual-aid-preview-nav" aria-label="Mutual Aid governance links">
        <Link to="/admin/mutual-aid/pilot-readiness">Readiness page</Link>
        <Link to="/admin/mutual-aid">Admin planning</Link>
        <Link to="/mutual-aid">Public overview</Link>
      </nav>

      <section className="mutual-aid-governance-grid" aria-label="Governance overview">
        {overviewCards.map((card) => (
          <article className="mutual-aid-card" key={card.label}>
            <p className="mutual-aid-kicker">{card.label}</p>
            <h2>{card.value}</h2>
            <p>{card.detail}</p>
          </article>
        ))}
      </section>

      <section className="mutual-aid-grid" aria-label="Governance documentation sections">
        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Required Documents</h2>
          <div className="mutual-aid-document-grid">{documents.map(([name, status, owner, reviewed, next]) => <div className="mutual-aid-document-card" key={name}><div className="mutual-aid-card__header"><h3>{name}</h3><GovernanceBadge>{status}</GovernanceBadge></div><p><strong>Owner:</strong> {owner}</p><p><strong>Last reviewed:</strong> {reviewed}</p><p><strong>Next review:</strong> {next}</p></div>)}</div>
        </article>

        <article className="mutual-aid-card">
          <h2>Standard Operating Procedures</h2>
          <div className="mutual-aid-sop-list">{sopItems.map((item, index) => <div key={item}><span>{index + 1}</span>{item}</div>)}</div>
        </article>

        <article className="mutual-aid-card">
          <h2>Legal & Compliance</h2>
          <div className="mutual-aid-checklist-grid">{complianceItems.map((item) => <label className="mutual-aid-check" key={item}><input type="checkbox" disabled /> <span>{item}</span></label>)}</div>
          <p className="mutual-aid-note">Disabled checks are informational only and do not save state.</p>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Committee Resources</h2>
          <div className="mutual-aid-document-grid mutual-aid-document-grid--compact">{resources.map(([title, summary]) => <div className="mutual-aid-document-card" key={title}><h3>{title}</h3><p>{summary}</p></div>)}</div>
        </article>

        <article className="mutual-aid-card">
          <h2>Decision Log</h2>
          <div className="mutual-aid-decision-timeline">{decisions.map(([date, text]) => <div key={date}><time>{date}</time><p>{text}</p></div>)}</div>
        </article>

        <article className="mutual-aid-card">
          <h2>Upcoming Reviews</h2>
          <div className="mutual-aid-review-schedule">{reviews.map(([title, date, detail]) => <div key={title}><time>{date}</time><strong>{title}</strong><p>{detail}</p></div>)}</div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Version History</h2>
          <div className="mutual-aid-version-table" role="table" aria-label="Example version history"><div role="row" className="mutual-aid-version-table__row mutual-aid-version-table__row--header"><span>Document</span><span>Version</span><span>Date</span><span>Status</span></div>{versions.map(([doc, version, date, status]) => <div role="row" className="mutual-aid-version-table__row" key={`${doc}-${version}`}><span>{doc}</span><span>{version}</span><span>{date}</span><span>{status}</span></div>)}</div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Activation Dependencies</h2>
          <p>Reference the existing <Link className="mutual-aid-inline-link" to="/admin/mutual-aid/pilot-readiness">Mutual Aid Pilot Readiness Workflow</Link>. This page does not duplicate readiness business logic.</p>
          <ul className="mutual-aid-list">{dependencies.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Next Phase</h2>
          <p>Future phases may include document storage, version management, approval workflows, and audit history. Those capabilities are not implemented in this planning-only center.</p>
        </article>
      </section>
    </main>
  );
}
