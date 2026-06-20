import React from "react";
import ApplicationCard from "../components/ApplicationCard";
import { applicationsByCategory } from "../data/applications";
import "../styles/applications.css";

export default function ApplicationsPage() {
  const groupedApplications = applicationsByCategory();

  return (
    <main className="applications-shell cosmic-readable-shell">
      <header className="applications-hero">
        <p className="section-kicker">Simba Operating System</p>
        <h1>Applications</h1>
        <p>
          Open the tools of the Community Operating System from one launcher. Simba develops people,
          connects people, coordinates people, and introduces specialized platforms when members are ready.
        </p>
      </header>

      <section className="applications-principle-panel">
        <article><span>Simba</span><strong>Community Operating System</strong><p>Member growth, community coordination, learning, culture, and readiness.</p></article>
        <article><span>External Platforms</span><strong>Connected, not absorbed</strong><p>Garvey, the Investment Platform, and PocketPT remain independent systems.</p></article>
        <article><span>Future Ready</span><strong>Reserved architecture</strong><p>Coming Soon applications are visible without creating fake functionality.</p></article>
      </section>

      {groupedApplications.map((group) => (
        <section className="application-category" key={group.category}>
          <div className="application-category__heading">
            <p className="section-kicker">Application Group</p>
            <h2>{group.category}</h2>
          </div>
          <div className="application-grid">
            {group.applications.map((application) => <ApplicationCard key={application.id} application={application} />)}
          </div>
        </section>
      ))}
    </main>
  );
}
