import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
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
  const [items, setItems] = useState([]);

  useEffect(() => {
    async function loadLibrary() {
      try {
        const response = await api("/audiobooks", { method: "GET", credentials: "include" });
        setItems(response.items || []);
      } catch {
        setItems([]);
      }
    }

    loadLibrary();
  }, []);

  return (
    <main className="library-shell">
      <div className="library-inner cosmic-readable-shell">
        <h1>Book + Audiobook Library</h1>
        <p>Your saved manuscripts and audiobooks stay in the system for reading, listening, and resume progress.</p>

        <div className="library-actions">
          <Link to="/study" className="library-pill library-pill--green">
            + Save New Book / Audiobook
          </Link>
          <Link to="/portal/decolonize" className="library-pill library-pill--gold">
            Open Decolonization Portal
          </Link>
        </div>

        <section className="saved-library-grid">
          {!items.length ? (
            <p className="saved-empty">No books saved yet. Start in Audiobook Studio to add your first title.</p>
          ) : (
            items.map((item) => (
              <article key={item.id} className="saved-book-card">
                <h3>{item.title}</h3>
                <p>{item.author}</p>
                <div className="saved-meta">
                  <span>{item.status}</span>
                  <span>{item.access_level}</span>
                  <span>{item.audio_chapter_count}/{item.chapter_count} voiced</span>
                </div>
                <div className="saved-actions">
                  <Link to={`/study?book=${item.id}`} className="library-pill phase-link">
                    Continue Reading/Listening →
                  </Link>
                </div>
              </article>
            ))
          )}
        </section>

        <h2 className="library-section-title">Decolonization Journey</h2>
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
