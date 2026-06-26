import React from "react";
import MutualAidFundProgressCard from "../components/MutualAidFundProgressCard";
import { MUTUAL_AID_STATUS } from "../mutualAidFundProgress";
import { readinessStages } from "./MutualAidPilotReadinessPage";
import "../styles/mutualAid.css";

const executiveSummaryCards = [
  { label: "Pilot Status", value: "Planning Only", detail: "Static readiness view" },
  { label: "Fund Status", value: "Not Active", detail: "No distributions before activation" },
  { label: "Activation Progress", value: "0%", detail: "Example progress only" },
  { label: "Readiness Score", value: "6 / 12", detail: "Illustrative internal score" },
  { label: "Documents Complete", value: "8", detail: "Example document count" },
  { label: "Remaining Tasks", value: "14", detail: "Example planning tasks" },
];

const timelineSteps = [
  "Planning",
  "Documentation",
  "Internal Review",
  "Committee Review",
  "Pilot Preparation",
  "Activation Review",
  "Pilot Launch",
];

const blockers = [
  "Funding threshold not reached",
  "Documentation review pending",
  "Governance approval pending",
  "Pilot participants not selected",
  "Training incomplete",
];

const governanceChecklist = [
  "Operating appendix reviewed",
  "Committee charter reviewed",
  "Conflict policy acknowledged",
  "Privacy safeguards reviewed",
  "Activation stop conditions reviewed",
  "Launch communications reviewed",
];

const committeeMembers = [
  { name: "Example Steward A", role: "Committee Chair", status: "Training planned" },
  { name: "Example Steward B", role: "Documentation Lead", status: "Review pending" },
  { name: "Example Steward C", role: "Member Support", status: "Pilot briefing pending" },
  { name: "Example Steward D", role: "Finance Observer", status: "Controls review pending" },
];

const riskRows = [
  { risk: "Members mistake planning screens for active aid", severity: "High", mitigation: "Prominent preview-only notices", status: "Monitoring" },
  { risk: "Governance review incomplete", severity: "High", mitigation: "Require committee review before activation", status: "Pending" },
  { risk: "Training materials not finalized", severity: "Medium", mitigation: "Complete pilot briefing packet", status: "Drafting" },
  { risk: "Launch messaging unclear", severity: "Medium", mitigation: "Review FAQ, terms, and announcement copy", status: "Planned" },
];

const communicationChecklist = [
  "FAQ prepared",
  "Member announcement drafted",
  "Terms reviewed",
  "Launch announcement",
  "Pilot briefing",
];

const kpiCards = [
  { label: "Eligible Members", value: "120" },
  { label: "Preview Requests", value: "18" },
  { label: "Planned Reviews", value: "6" },
  { label: "Planned Reports", value: "4" },
  { label: "Pilot Size", value: "25 members" },
  { label: "Target Launch Window", value: "TBD" },
];

const notices = [
  "Preview Only",
  "Not Active",
  "Building Toward Activation",
  "No distributions before activation",
  "Support is reviewed and never guaranteed",
  "Pilot planning interface only",
];

function DisabledChecklist({ items }) {
  return (
    <div className="mutual-aid-dashboard-checklist">
      {items.map((item) => (
        <label className="mutual-aid-check" key={item}>
          <input type="checkbox" disabled />
          <span>{item}</span>
        </label>
      ))}
    </div>
  );
}

export default function MutualAidOperationsDashboard() {
  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--operations">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-operations-title">
        <p className="mutual-aid-kicker">Admin Only · Planning Dashboard</p>
        <h1 id="mutual-aid-operations-title">Mutual Aid Operations Dashboard</h1>
        <p className="mutual-aid-subtitle">
          Static pilot readiness dashboard for previewing Mutual Aid operations planning in one place. No requests,
          reviews, uploads, approvals, payments, ledgers, wallets, or backend integrations are active here.
        </p>
        <div className="mutual-aid-status" aria-label="Current status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>Status: {MUTUAL_AID_STATUS}</span>
        </div>
      </section>

      <section className="mutual-aid-warning cosmic-readable-shell" aria-label="Operations dashboard notices">
        <div className="mutual-aid-notice-grid">
          {notices.map((notice) => <strong key={notice}>{notice}</strong>)}
        </div>
      </section>

      <section className="mutual-aid-dashboard-grid" aria-label="Mutual Aid operations planning dashboard">
        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Executive Summary</h2>
          <div className="mutual-aid-executive-grid">
            {executiveSummaryCards.map((card) => (
              <div className="mutual-aid-metric-card" key={card.label}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
                <small>{card.detail}</small>
              </div>
            ))}
          </div>
        </article>

        <MutualAidFundProgressCard />

        <article className="mutual-aid-card">
          <h2>Pilot Timeline</h2>
          <ol className="mutual-aid-timeline">
            {timelineSteps.map((step) => <li key={step}>{step}</li>)}
          </ol>
          <p className="mutual-aid-note">Current step: <strong>Building Toward Activation</strong></p>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Readiness Summary</h2>
          <div className="mutual-aid-readiness-board">
            {readinessStages.map((stage, index) => (
              <div className="mutual-aid-readiness-stage" key={stage}>
                <input type="checkbox" disabled />
                <span className="mutual-aid-readiness-stage__number">{index + 1}</span>
                <span>{stage}</span>
                <em>Read-only operations summary</em>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Activation Blockers</h2>
          <div className="mutual-aid-blocker-list">
            {blockers.map((blocker) => <div className="mutual-aid-blocker-card" key={blocker}>{blocker}</div>)}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Governance Checklist</h2>
          <DisabledChecklist items={governanceChecklist} />
        </article>

        <article className="mutual-aid-card">
          <h2>Committee</h2>
          <div className="mutual-aid-committee-list">
            {committeeMembers.map((member) => (
              <div key={member.name}>
                <strong>{member.name}</strong>
                <span>{member.role}</span>
                <small>{member.status}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Communication Checklist</h2>
          <DisabledChecklist items={communicationChecklist} />
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Risk Register</h2>
          <div className="mutual-aid-risk-table" role="table" aria-label="Static risk register">
            <div className="mutual-aid-risk-row mutual-aid-risk-row--header" role="row">
              <span>Risk</span><span>Severity</span><span>Mitigation</span><span>Status</span>
            </div>
            {riskRows.map((row) => (
              <div className="mutual-aid-risk-row" role="row" key={row.risk}>
                <span>{row.risk}</span><span>{row.severity}</span><span>{row.mitigation}</span><span>{row.status}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>KPI Cards</h2>
          <div className="mutual-aid-executive-grid">
            {kpiCards.map((card) => (
              <div className="mutual-aid-metric-card" key={card.label}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
                <small>Example metric only</small>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Next Steps</h2>
          <p>
            The next implementation phase may plan requests, review workflow, document upload, and disbursement workflow.
            Those features are not implemented in this dashboard and require separate approval before any live Mutual Aid
            operations can begin.
          </p>
        </article>
      </section>
    </main>
  );
}
