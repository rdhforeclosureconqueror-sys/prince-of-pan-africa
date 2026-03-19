import React, { useMemo } from "react";
import RoleMeter from "./RoleMeter";
import CoachingPanel from "./CoachingPanel";
import { ROLE_LABELS } from "../../services/leadershipService";

export default function ResultsDashboard({ result }) {
  const sortedRoles = useMemo(
    () =>
      Object.entries(result.percentages || {})
        .map(([key, value]) => ({ key, label: ROLE_LABELS[key] || key, value: Number(value) || 0 }))
        .sort((a, b) => b.value - a.value),
    [result.percentages],
  );

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

      <section className="role-meters">
        <h3>Role Distribution</h3>
        {sortedRoles.map((role) => (
          <RoleMeter key={role.key} label={role.label} value={role.value} />
        ))}
      </section>

      <CoachingPanel coaching={result.coaching} />
    </div>
  );
}
