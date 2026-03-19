import React, { useMemo } from "react";
import RoleMeter from "./RoleMeter";
import CoachingPanel from "./CoachingPanel";
import CircleProgress from "./CircleProgress";
import { ROLE_LABELS } from "../../services/leadershipService";

const ROLE_IMAGES = {
  Architect: "/images/roles/architect.svg",
  Operator: "/images/roles/operator.svg",
  Steward: "/images/roles/steward.svg",
  Builder: "/images/roles/builder.svg",
  Connector: "/images/roles/connector.svg",
  Protector: "/images/roles/protector.svg",
  Nurturer: "/images/roles/nurturer.svg",
  Educator: "/images/roles/educator.svg",
  ResourceGenerator: "/images/roles/resourcegenerator.svg",
};

export default function ResultsDashboard({ result }) {
  const sortedRoles = useMemo(
    () =>
      Object.entries(result.percentages || {})
        .map(([key, value]) => ({ key, label: ROLE_LABELS[key] || key, value: Number(value) || 0 }))
        .sort((a, b) => b.value - a.value),
    [result.percentages],
  );

  const topThree = sortedRoles.slice(0, 3);

  return (
    <div className="results-dashboard">
      <section className="identity-cards">
        <article>
          <h4>Primary Role</h4>
          <p>{result.roles?.primary}</p>
        </article>
        <article>
          <h4>Secondary Role</h4>
          <p>{result.roles?.secondary}</p>
        </article>
        <article>
          <h4>Growth Role</h4>
          <p>{result.roles?.growth}</p>
        </article>
        <article>
          <h4>Shadow Role</h4>
          <p>{result.roles?.shadow}</p>
        </article>
      </section>

      <section className="top-three-section">
        <h3>Top 3 Leadership Energies</h3>
        <div className="top-three-grid">
          {topThree.map((role) => (
            <CircleProgress
              key={role.key}
              label={role.label}
              value={role.value}
              image={ROLE_IMAGES[role.label]}
            />
          ))}
        </div>
      </section>

      <section className="role-meters">
        <h3>Role Distribution</h3>
        {sortedRoles.map((role) => (
          <RoleMeter key={role.key} label={role.label} value={role.value} />
        ))}
      </section>

      <CoachingPanel coaching={result.coaching} insights={result.insights} />
    </div>
  );
}
