import React from "react";
import { Link } from "react-router-dom";
import "../styles/library.css";

const PHASES = [
  {
    id: "phase-1",
    title: "Phase I — Foundation (Days 1–5)",
    desc: "Knowledge of Self, nervous system regulation, and narrative audit basics.",
  },
  {
    id: "phase-2",
    title: "Phase II — Regional Systems (Days 6–12)",
    desc: "Reintegration through African-aligned body–breath–mind practices and context.",
  },
  {
    id: "phase-3",
    title: "Phase III — Power Pattern Audit (Days 13–18)",
    desc: "Track distortions: rename, moralize, sanitize, erase, launder attribution.",
  },
  {
    id: "phase-4",
    title: "Phase IV — Repair & Reconstruction (Days 19–24)",
    desc: "Rebuild living practice: ethics, community coherence, modern application.",
  },
  {
    id: "phase-5",
    title: "Phase V — Integration & Teaching (Days 25–30)",
    desc: "Turn learning into service: curriculum, family practice, community delivery.",
  },
];

export default function LibraryDecolonize() {
  return (
    <main className="library-shell">
      <div className="library-inner cosmic-readable-shell">
        <h1>Decolonization Library</h1>
        <p>5 phases → click into the portal when you’re ready to run the process.</p>

        <div className="library-actions">
          <Link to="/portal/decolonize" className="library-pill library-pill--green">
            ▶ Start Decolonization Portal
          </Link>

          <Link to="/membership" className="library-pill library-pill--gold">
            📅 View 30-Day Plan
          </Link>
        </div>

        <div className="phase-grid">
          {PHASES.map((phase) => (
            <article key={phase.id} className="phase-card">
              <div className="phase-title">{phase.title}</div>
              <div className="phase-desc">{phase.desc}</div>

              <div className="phase-link-wrap">
                <Link to="/portal/decolonize" className="library-pill phase-link">
                  Open Portal →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
