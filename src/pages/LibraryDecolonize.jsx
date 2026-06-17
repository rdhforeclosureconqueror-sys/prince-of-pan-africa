import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/api";
import { API_BASE_URL } from "../config";
import { ENABLE_TEXT_BOOK_ORGANIZER } from "../config";
import PublicEngagementBar from "../components/PublicEngagementBar";
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

const ACCESS_LABELS = {
  public: "Public",
  free: "Free",
  subscription: "Subscription",
  member: "Community Member",
  subscriber: "Builder Member",
  builder_member: "Builder Member",
  private: "Private",
  purchased: "Purchased",
};

function formatAccessLevel(accessLevel) {
  return ACCESS_LABELS[accessLevel] || accessLevel || "Unknown";
}

const DEFAULT_COVER_PATH = "/book-covers/library-placeholder.svg";

function mediaUrl(path) {
  if (!path) return DEFAULT_COVER_PATH;
  if (path.startsWith("http")) return path;
  if (path.startsWith("/static/")) return `${API_BASE_URL}${path}`;
  return path;
}

function handleCoverError(event) {
  if (event.currentTarget.src.endsWith(DEFAULT_COVER_PATH)) return;
  event.currentTarget.src = DEFAULT_COVER_PATH;
}

function shortDescription(item) {
  return item.description || "Saved for reading, listening, and resume progress.";
}

function readingTime(item) {
  return `${Math.max(1, Math.ceil((item.total_characters || 0) / 9000))} min read`;
}

function listeningTime(item) {
  return item.audio_chapter_count > 0 ? `${item.audio_chapter_count} audio section${item.audio_chapter_count === 1 ? "" : "s"}` : "Audio coming soon";
}

export default function LibraryDecolonize({ canAccessOrganizer = false, authChecked = false, user = null }) {
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
        <p>Browse public books, preview audiobooks, and share the Simba wa Ujamaa experience with your community.</p>

        <div className="library-actions">
          <Link to="/study" className="library-pill library-pill--green">
            + Save New Book / Audiobook
          </Link>
          <Link to="/portal/decolonize" className="library-pill library-pill--gold">
            Open Decolonization Portal
          </Link>
          {ENABLE_TEXT_BOOK_ORGANIZER && authChecked && canAccessOrganizer ? (
            <Link to="/library/organizer" className="library-pill">
              Text Book Organizer · Upload Book Text
            </Link>
          ) : null}
          {ENABLE_TEXT_BOOK_ORGANIZER && authChecked && user && !canAccessOrganizer ? (
            <span className="library-access-note">Text Book Organizer requires Builder Member or admin access.</span>
          ) : null}
        </div>

        <section className="saved-library-grid">
          {!items.length ? (
            <p className="saved-empty">No public books are available yet. Check back soon as the library grows.</p>
          ) : (
            items.map((item) => (
              <article key={item.id} className="saved-book-card saved-book-card--cover">
                <Link to={`/study?book=${item.id}`} className="saved-cover-link" aria-label={`Open ${item.title}`}>
                  <img src={mediaUrl(item.cover_image_path)} alt={`${item.title} cover`} className="saved-cover-thumb" onError={handleCoverError} />
                  {item.audio_chapter_count > 0 ? <span className="saved-audio-badge">Audiobook available</span> : <span className="saved-audio-badge saved-audio-badge--pending">Audio pending</span>}
                </Link>
                <div className="saved-book-card-body">
                  <h3>{item.title}</h3>
                  <p className="saved-author">{item.author}</p>
                  <p className="saved-description">{shortDescription(item)}</p>
                  <div className="saved-meta">
                    <span>{readingTime(item)}</span>
                    <span>{listeningTime(item)}</span>
                    <span>{item.audio_chapter_count}/{item.chapter_count} voiced</span>
                  </div>
                  <span className={`library-visibility-badge library-visibility-badge--${item.access_level}`}>
                    {formatAccessLevel(item.access_level)}
                  </span>
                  <PublicEngagementBar
                    contentType="book"
                    contentId={item.id}
                    title={item.title}
                    text={`Explore ${item.title} in the Simba wa Ujamaa public library.`}
                    path={`/study?book=${item.id}`}
                  />
                  <div className="saved-actions">
                    <Link to={`/study?book=${item.id}`} className="library-pill phase-link">
                      Read / Listen →
                    </Link>
                  </div>
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
