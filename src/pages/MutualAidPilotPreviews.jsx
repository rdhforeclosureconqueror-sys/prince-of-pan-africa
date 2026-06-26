import React from "react";
import { Link } from "react-router-dom";
import MutualAidFundProgressCard from "../components/MutualAidFundProgressCard";
import { activationRequirements, formatMutualAidCurrency, MUTUAL_AID_ACTIVATION_THRESHOLD, MUTUAL_AID_STATUS } from "../mutualAidFundProgress";
import "../styles/mutualAid.css";

const memberLinks = [
  { to: "/mutual-aid/request-preview", label: "Request preview" },
  { to: "/mutual-aid/nominate-preview", label: "Nomination preview" },
  { to: "/mutual-aid/requests-preview", label: "My requests preview" },
];

const adminLinks = [
  { to: "/admin/mutual-aid/review-preview", label: "Review queue preview" },
  { to: "/admin/mutual-aid/disbursements-preview", label: "Support tracking preview" },
  { to: "/admin/mutual-aid/reports-preview", label: "Impact reporting preview" },
];

const categories = ["Emergency Relief", "Education and Preparedness", "Member Hardship Support"];
const statuses = ["Preview Only", "Not Active", MUTUAL_AID_STATUS];
const sampleRows = [
  { title: "Emergency home repair", status: "Example only — Under review", amount: "$175" },
  { title: "Preparedness supplies", status: "Example only — More information needed", amount: "$80" },
  { title: "Transportation support", status: "Example only — Closed", amount: "$45" },
];

function PreviewShell({ audience = "member", title, subtitle, children }) {
  const links = audience === "admin" ? adminLinks : memberLinks;

  return (
    <main className={`mutual-aid-page mutual-aid-page--preview ${audience === "admin" ? "mutual-aid-page--admin" : ""}`}>
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-preview-title">
        <p className="mutual-aid-kicker">Preview Only · Not Active</p>
        <h1 id="mutual-aid-preview-title">{title}</h1>
        <p className="mutual-aid-subtitle">{subtitle}</p>
        <div className="mutual-aid-status" aria-label="Current status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>{MUTUAL_AID_STATUS}</span>
        </div>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell" aria-label="Preview-only safeguards">
        <strong>Preview Only:</strong> Requests are not open yet. This screen is Not Active and is Building Toward Activation.
        <br />
        <strong>No distributions before activation:</strong> Support is reviewed and not guaranteed. Activation requires the {formatMutualAidCurrency(MUTUAL_AID_ACTIVATION_THRESHOLD)} threshold plus approved policy, governance process, accounting controls, privacy rules, approval controls, trained committee, and legal/tax/compliance review before public launch.
      </section>

      <nav className="mutual-aid-preview-nav" aria-label={`${audience} preview pages`}>
        {links.map((link) => (
          <Link key={link.to} to={link.to}>{link.label}</Link>
        ))}
      </nav>

      <section className="mutual-aid-grid" aria-label="Preview content">
        {children}
      </section>
    </main>
  );
}

function PreviewBadgeList() {
  return (
    <div className="mutual-aid-badges" aria-label="Preview status labels">
      {statuses.map((status) => <span key={status}>{status}</span>)}
    </div>
  );
}

function DisabledField({ label, type = "text", value = "", children }) {
  return (
    <label className="mutual-aid-field">
      <span>{label}</span>
      {children || <input type={type} value={value} disabled readOnly />}
    </label>
  );
}

function DisabledRequestFields({ nomination = false }) {
  return (
    <article className="mutual-aid-card mutual-aid-card--wide">
      <h2>{nomination ? "Future nomination details" : "Future request details"}</h2>
      <p>This display-only layout shows a possible future flow. It cannot save, send, attach files, or create records.</p>
      <div className="mutual-aid-form-grid">
        {nomination ? <DisabledField label="Member being nominated" value="Example member name" /> : null}
        <DisabledField label="Support category">
          <select disabled defaultValue="">
            <option value="">Select a future category</option>
            {categories.map((category) => <option key={category}>{category}</option>)}
          </select>
        </DisabledField>
        <DisabledField label="Requested support amount" value="$0" />
        <DisabledField label="Preferred support method">
          <select disabled defaultValue="">
            <option value="">Future policy-approved method</option>
            <option>Pay provider/vendor directly</option>
            <option>Reimbursement after receipt if approved by policy</option>
            <option>Direct member support if allowed by policy</option>
            <option>Voucher or restricted support</option>
            <option>Other policy-reviewed method</option>
          </select>
        </DisabledField>
        <DisabledField label="Brief need summary">
          <textarea disabled value="Example-only summary placeholder. Requests are not open yet." readOnly />
        </DisabledField>
      </div>
      <button className="mutual-aid-disabled-button" type="button" disabled>{nomination ? "Nomination not active" : "Requests are not open yet"}</button>
    </article>
  );
}

export function MutualAidRequestPreviewPage() {
  return (
    <PreviewShell title="Request Mutual Aid Support" subtitle="A disabled member request preview for a later approved phase.">
      <article className="mutual-aid-card"><h2>Member notice</h2><p>This request flow is not active yet. If a future phase approves it, members may use a reviewed process to request support.</p><PreviewBadgeList /></article>
      <DisabledRequestFields />
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Activation checklist</h2><ul className="mutual-aid-list">{activationRequirements.map((item) => <li key={item}>{item}</li>)}</ul></article>
    </PreviewShell>
  );
}

export function MutualAidNominatePreviewPage() {
  return (
    <PreviewShell title="Nominate a Member for Support" subtitle="A disabled nomination preview for respectful future community care.">
      <article className="mutual-aid-card"><h2>Nomination notice</h2><p>A nomination does not guarantee aid. The nominated member may need to confirm their request and agree to review.</p><PreviewBadgeList /></article>
      <DisabledRequestFields nomination />
    </PreviewShell>
  );
}

export function MutualAidRequestsPreviewPage() {
  return (
    <PreviewShell title="My Mutual Aid Requests" subtitle="An empty member preview showing that live request history is not active.">
      <article className="mutual-aid-card mutual-aid-card--wide mutual-aid-empty-state"><h2>No active requests</h2><p>Requests are not open yet, so there is no live request history. Future entries would appear only after activation and approval of the workflow.</p><Link className="mutual-aid-link-button" to="/mutual-aid/request-preview">View disabled request preview</Link></article>
      <MutualAidFundProgressCard />
    </PreviewShell>
  );
}

export function MutualAidReviewPreviewPage() {
  return (
    <PreviewShell audience="admin" title="Mutual Aid Review Queue" subtitle="An admin-only disabled preview of future committee review readiness.">
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Example-only queue</h2><div className="mutual-aid-table" role="table" aria-label="Example-only review rows">{sampleRows.map((row) => <div className="mutual-aid-table__row" role="row" key={row.title}><span>{row.title}</span><span>{row.status}</span><span>{row.amount}</span><button type="button" disabled>Review not active</button></div>)}</div></article>
      <article className="mutual-aid-card"><h2>Review safeguards</h2><p>No real review queue, approval workflow, notifications, or records are connected to this preview.</p></article>
    </PreviewShell>
  );
}

export function MutualAidDisbursementsPreviewPage() {
  return (
    <PreviewShell audience="admin" title="Mutual Aid Support Tracking" subtitle="A disabled admin preview for future manual support status tracking.">
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>No distributions before activation</h2><p>This page does not move money, trigger fund movement, create accounting entries, or track real support. Rows below are example only.</p><div className="mutual-aid-table" role="table" aria-label="Example-only support tracking rows">{sampleRows.slice(0, 2).map((row) => <div className="mutual-aid-table__row" role="row" key={row.title}><span>{row.title}</span><span>Example only — Preparing support</span><span>{row.amount}</span><button type="button" disabled>Tracking not active</button></div>)}</div></article>
    </PreviewShell>
  );
}

export function MutualAidReportsPreviewPage() {
  return (
    <PreviewShell audience="admin" title="Mutual Aid Impact Reporting" subtitle="A disabled admin preview for future anonymized reporting concepts.">
      <article className="mutual-aid-card"><h2>Preview metrics</h2><dl className="mutual-aid-preview-metrics"><div><dt>Requests reviewed</dt><dd>0</dd></div><div><dt>Support completed</dt><dd>0</dd></div><div><dt>Average review time</dt><dd>Not active</dd></div></dl></article>
      <article className="mutual-aid-card mutual-aid-card--wide"><h2>Reporting status</h2><p>No live reporting, real review data, fund movement data, or member records are available. Future reporting requires approved privacy rules and governance review.</p></article>
    </PreviewShell>
  );
}
