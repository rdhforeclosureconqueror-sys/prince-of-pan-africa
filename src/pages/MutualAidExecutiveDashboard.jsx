import React from "react";
import { Link } from "react-router-dom";
import { readinessStages } from "./MutualAidPilotReadinessPage";
import "../styles/mutualAid.css";

const executiveKpis = [
  { label: "Overall Readiness", value: "68%", detail: "Example aggregate only" },
  { label: "Governance Status", value: "In Review", detail: "Policy and committee planning" },
  { label: "Operations Status", value: "Draft", detail: "SOP and staffing readiness" },
  { label: "Pilot Status", value: "Planning", detail: "Readiness shell not active" },
  { label: "Risk Level", value: "Medium", detail: "Static planning risk" },
  { label: "Launch Confidence", value: "Cautious", detail: "Executive review required" },
];

const planningModules = [
  { title: "Pilot Readiness", href: "/admin/mutual-aid/pilot-readiness", completion: "58%", owner: "Pilot Lead", updated: "Jun 18, 2026", status: "Readiness stages in review" },
  { title: "Operations Dashboard", href: "/admin/mutual-aid/dashboard", completion: "64%", owner: "Operations Lead", updated: "Jun 20, 2026", status: "Planning dashboard drafted" },
  { title: "Governance Center", href: "/admin/mutual-aid/governance", completion: "72%", owner: "Governance Lead", updated: "Jun 22, 2026", status: "Documents under review" },
];

const launchChecklist = [
  "Governance complete",
  "Policies complete",
  "SOPs complete",
  "Communications complete",
  "Committee ready",
  "Risk review complete",
  "Pilot complete",
  "Executive approval",
];

const crossProgramRisks = [
  { risk: "Planning screens are misunderstood as live Mutual Aid support", impact: "High", owner: "Communications", status: "Preview notices displayed" },
  { risk: "Governance dependencies remain unresolved", impact: "High", owner: "Governance Lead", status: "In review" },
  { risk: "Operations staffing assumptions are not confirmed", impact: "Medium", owner: "Operations Lead", status: "Drafting" },
  { risk: "Pilot readiness stages need external confirmation", impact: "Medium", owner: "Pilot Lead", status: "Pending confirmation" },
];

const timelineMilestones = ["Planning", "Governance", "Pilot", "Operations", "Launch Review", "Public Launch"];

const scorecards = [
  { label: "Governance", value: 72 },
  { label: "Operations", value: 64 },
  { label: "Policy", value: 70 },
  { label: "Communications", value: 55 },
  { label: "Technology", value: 60 },
  { label: "Committee", value: 48 },
  { label: "Compliance", value: 62 },
  { label: "Pilot", value: 58 },
  { label: "Overall Readiness", value: 68 },
];

const decisionItems = [
  { title: "Approve launch readiness criteria", owner: "Executive Sponsor", status: "Awaiting review" },
  { title: "Confirm committee preparedness", owner: "Governance Lead", status: "Inputs pending" },
  { title: "Accept pilot stop conditions", owner: "Pilot Lead", status: "Draft decision" },
];

const dependencies = [
  { source: "Pilot Readiness", detail: `${readinessStages.length} readiness stages must be confirmed outside this static dashboard before activation.` },
  { source: "Operations Dashboard", detail: "Operations planning, communication tasks, blockers, and risk register summaries must be reviewed before launch review." },
  { source: "Governance Center", detail: "Required documents, policy reviews, compliance checks, and committee resources must be complete before public launch." },
];

const upcomingMilestones = [
  { date: "Jul 8, 2026", title: "Governance packet review", detail: "Example executive preparation milestone" },
  { date: "Jul 22, 2026", title: "Pilot readiness checkpoint", detail: "Example static readiness checkpoint" },
  { date: "Aug 5, 2026", title: "Operations tabletop", detail: "Example launch operations planning event" },
  { date: "Sep 12, 2026", title: "Launch review", detail: "Example executive go/no-go review" },
];

const notices = ["Preview Only", "Planning Dashboard", "No backend integration", "No persistence", "No approvals", "No workflow", "No launch automation"];
const futurePhases = ["Live metrics", "Real readiness scoring", "Automated reporting", "Executive approvals", "Notifications", "Calendar integration", "Document integration"];

function DisabledChecklist({ items }) {
  return (
    <div className="mutual-aid-launch-checklist">
      {items.map((item) => (
        <label className="mutual-aid-check" key={item}>
          <input type="checkbox" disabled />
          <span>{item}</span>
        </label>
      ))}
    </div>
  );
}

export default function MutualAidExecutiveDashboard() {
  return (
    <main className="mutual-aid-page mutual-aid-page--admin mutual-aid-page--executive">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-executive-title">
        <p className="mutual-aid-kicker">Admin Only · Planning Dashboard</p>
        <h1 id="mutual-aid-executive-title">Mutual Aid Executive Launch Readiness Dashboard</h1>
        <p className="mutual-aid-subtitle">
          Static executive view summarizing existing Mutual Aid planning areas. This page references Pilot Readiness,
          Operations Dashboard, and Governance Center content without creating live launch workflow.
        </p>
        <div className="mutual-aid-badges" aria-label="Executive dashboard notices">
          {notices.map((notice) => <span key={notice}>{notice}</span>)}
        </div>
      </section>

      <section className="mutual-aid-grid" aria-label="Executive launch readiness sections">
        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Executive Summary</h2>
          <div className="mutual-aid-executive-kpi-grid">
            {executiveKpis.map((card) => (
              <div className="mutual-aid-executive-summary-card" key={card.label}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
                <small>{card.detail}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Planning Modules</h2>
          <div className="mutual-aid-dependency-grid">
            {planningModules.map((module) => (
              <Link className="mutual-aid-dependency-card" to={module.href} key={module.title}>
                <h3>{module.title}</h3>
                <p><strong>Completion:</strong> {module.completion}</p>
                <p><strong>Owner:</strong> {module.owner}</p>
                <p><strong>Last updated:</strong> {module.updated}</p>
                <p><strong>Status:</strong> {module.status}</p>
              </Link>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Launch Checklist</h2>
          <DisabledChecklist items={launchChecklist} />
          <p className="mutual-aid-note">Disabled controls are examples only and do not save state.</p>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Cross-Program Risks</h2>
          <div className="mutual-aid-risk-table" role="table" aria-label="Static cross-program risks">
            <div className="mutual-aid-risk-row mutual-aid-risk-row--header" role="row"><span>Risk</span><span>Impact</span><span>Owner</span><span>Status</span></div>
            {crossProgramRisks.map((row) => (
              <div className="mutual-aid-risk-row" role="row" key={row.risk}><span>{row.risk}</span><span>{row.impact}</span><span>{row.owner}</span><span>{row.status}</span></div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Executive Timeline</h2>
          <ol className="mutual-aid-milestone-timeline">
            {timelineMilestones.map((milestone) => <li key={milestone}>{milestone}</li>)}
          </ol>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Readiness Scorecard</h2>
          <div className="mutual-aid-readiness-scorecards">
            {scorecards.map((score) => (
              <div className="mutual-aid-readiness-score" key={score.label}>
                <div><strong>{score.label}</strong><span>{score.value}%</span></div>
                <progress value={score.value} max="100">{score.value}%</progress>
              </div>
            ))}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Decision Items</h2>
          <div className="mutual-aid-executive-decisions">
            {decisionItems.map((item) => <div key={item.title}><h3>{item.title}</h3><p>{item.owner}</p><small>{item.status}</small></div>)}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Dependencies</h2>
          <div className="mutual-aid-dependency-grid">
            {dependencies.map((dependency) => <div className="mutual-aid-dependency-card" key={dependency.source}><h3>{dependency.source}</h3><p>{dependency.detail}</p></div>)}
          </div>
        </article>

        <article className="mutual-aid-card">
          <h2>Upcoming Milestones</h2>
          <div className="mutual-aid-review-schedule">
            {upcomingMilestones.map((item) => <div key={item.title}><time>{item.date}</time><strong>{item.title}</strong><p>{item.detail}</p></div>)}
          </div>
        </article>

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Future Phases Not Implemented</h2>
          <ul className="mutual-aid-list">{futurePhases.map((phase) => <li key={phase}>{phase}</li>)}</ul>
        </article>
      </section>
    </main>
  );
}
