import React, { useMemo, useState } from "react";
import "../styles/library.css";
import { getAllSampleMemberBehavioralProfiles } from "../data/memberBehavioralProfiles";
import { getAllRoleBlueprints } from "../data/mutualAidRoleBlueprints";
import { interpretMemberRoleAlignment } from "../data/roleInterpretationEngine";

function ReportList({ title, items, emptyText = "No items to show yet." }) {
  return (
    <section className="library-card role-review-panel">
      <h2>{title}</h2>
      {items?.length ? <ul>{items.map((item) => <li key={typeof item === "string" ? item : item.name}>{typeof item === "string" ? item : item.reason}</li>)}</ul> : <p>{emptyText}</p>}
    </section>
  );
}

export default function MutualAidRoleReviewPage() {
  const members = getAllSampleMemberBehavioralProfiles();
  const roles = getAllRoleBlueprints();
  const [memberKey, setMemberKey] = useState(members[0]?.key || "");
  const [roleKey, setRoleKey] = useState("treasurer");

  const selectedMember = members.find((member) => member.key === memberKey) || members[0];
  const report = useMemo(() => interpretMemberRoleAlignment(selectedMember, roleKey), [selectedMember, roleKey]);

  if (!report) {
    return <main className="library-shell"><section className="library-inner cosmic-readable-shell"><h1>Role Review</h1><p>Select a member and role to begin interpretation.</p></section></main>;
  }

  return (
    <main className="library-shell">
      <section className="library-inner cosmic-readable-shell role-review-shell">
        <p className="library-pill library-pill--green">Internal Phase 1C preview</p>
        <h1>Mutual Aid Role Review</h1>
        <p>
          Compare a member behavioral profile with a role blueprint. This page interprets evidence for community
          discussion only; it does not rank, score, or automatically appoint anyone.
        </p>

        <div className="role-review-selectors" aria-label="Role review selectors">
          <label>
            Selected member
            <select value={memberKey} onChange={(event) => setMemberKey(event.target.value)}>
              {members.map((member) => <option key={member.key} value={member.key}>{member.displayName}</option>)}
            </select>
          </label>
          <label>
            Selected role
            <select value={roleKey} onChange={(event) => setRoleKey(event.target.value)}>
              {roles.map((role) => <option key={role.key} value={role.key}>{role.displayName}</option>)}
            </select>
          </label>
        </div>

        <section className="library-card role-review-hero">
          <div>
            <p className="section-kicker">Overall Alignment</p>
            <h2>{report.overallAlignment}</h2>
            <p><strong>{report.memberName}</strong> reviewed for <strong>{report.roleName}</strong>: {report.rolePurpose}</p>
            <p>{report.archetypeInterpretation}</p>
          </div>
          <div className="role-review-confidence">
            <span>Behavioral Confidence</span>
            <strong>{report.confidence}</strong>
            <p>{report.confidenceExplanation}</p>
          </div>
        </section>

        <section className="library-card role-review-panel">
          <h2>Why This Alignment Exists</h2>
          <ul>{report.whyThisAlignmentExists.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>

        <div className="library-grid role-review-grid">
          <ReportList title="Strengths Already Demonstrated" items={report.strengthsAlreadyDemonstrated} />
          <ReportList title="Areas That Could Be Strengthened" items={report.areasThatCouldBeStrengthened} />
          <section className="library-card role-review-panel">
            <h2>Missing Assessment Evidence</h2>
            {report.missingAssessmentEvidence.length ? (
              <>
                <p>Additional assessment evidence would improve confidence.</p>
                <ul>{report.missingAssessmentEvidence.map((item) => <li key={item.name}><strong>{item.name}:</strong> {item.reason}</li>)}</ul>
              </>
            ) : <p>Recommended assessment evidence for this role is currently available.</p>}
          </section>
          <ReportList title="Suggested Growth Path" items={report.suggestedGrowthPath} />
          <section className="library-card role-review-panel">
            <h2>Handbook Connections</h2>
            <ul>{report.handbookConnections.map((point) => <li key={point.chapterKey}><strong>{point.chapterLabel}</strong> — {point.connection}</li>)}</ul>
          </section>
          <section className="library-card role-review-panel">
            <h2>Complementary Team Members</h2>
            <p>This member may work especially well alongside teammates who bring complementary strengths:</p>
            <ul>{report.complementaryTeamMembers.map((type) => <li key={type}>{type}</li>)}</ul>
          </section>
        </div>

        <p className="role-review-reminder">{report.communityDecisionReminder}</p>
      </section>
    </main>
  );
}
