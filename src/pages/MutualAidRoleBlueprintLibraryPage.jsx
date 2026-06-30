import React from "react";
import "../styles/library.css";
import {
  getAllRoleBlueprints,
  HANDBOOK_CHAPTERS,
} from "../data/mutualAidRoleBlueprints";

function ListBlock({ title, items }) {
  return (
    <div>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

export default function MutualAidRoleBlueprintLibraryPage() {
  const roles = getAllRoleBlueprints();

  return (
    <main className="library-shell">
      <section className="library-inner cosmic-readable-shell">
        <p className="library-pill library-pill--green">Internal Phase 1A preview</p>
        <h1>Mutual Aid Society Role Blueprint Library</h1>
        <p>
          Static behavioral role requirements for future role-fit comparison. This preview does not score members,
          assign roles, create badges, or change the 100-Day Handbook.
        </p>
        <p>{roles.length} role blueprints connected to {Object.keys(HANDBOOK_CHAPTERS).length} handbook checkpoints.</p>

        <div className="library-grid">
          {roles.map((role) => (
            <article className="library-card" key={role.key}>
              <p className="library-pill">{role.key}</p>
              <h2>{role.displayName}</h2>
              <p>{role.purpose}</p>
              <ListBlock title="Responsibilities" items={role.coreResponsibilities} />
              <ListBlock title="Required traits" items={role.requiredBehavioralTraits} />
              <ListBlock title="Recommended assessments" items={role.recommendedAssessments} />
              <ListBlock title="Growth recommendations" items={role.growthRecommendations} />
              <div>
                <h3>100-Day chapter connections</h3>
                <ul>
                  {role.handbookConnectionPoints.map((point) => (
                    <li key={point.chapterKey}>{point.chapterLabel}</li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
