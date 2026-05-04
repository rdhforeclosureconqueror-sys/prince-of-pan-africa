import React, { useState } from "react";
import { api } from "../api/api";
import "../styles/library.css";

export default function LibraryOrganizer() {
  const [title, setTitle] = useState("Untitled");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null);

  async function handleOrganize() {
    setLoading(true);
    setError("");
    setPreview(null);
    try {
      const ingest = await api("/audiobooks/organizer/ingest-text", {
        method: "POST",
        body: JSON.stringify({ title, text }),
      });

      const plan = await api("/audiobooks/organizer/propose-plan", {
        method: "POST",
        body: JSON.stringify({ document_id: ingest.document.id, plan_name: "Default plan" }),
      });

      const phase3Preview = await api("/audiobooks/organizer/preview", {
        method: "POST",
        body: JSON.stringify({ document_id: ingest.document.id, plan_id: plan.plan_id }),
      });

      setPreview(phase3Preview);
    } catch (err) {
      setError(err?.message || "Organizer request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="library-shell">
      <div className="library-inner cosmic-readable-shell">
        <h1>Text Book Organizer</h1>
        <p>Your original words are preserved. Formatting and organization only.</p>

        <label>Working title</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} className="save-input" />

        <label>Paste manuscript text</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={14}
          className="save-textarea"
          placeholder="Paste paragraph-based text here..."
        />

        <div className="library-actions">
          <button type="button" className="library-pill library-pill--green" onClick={handleOrganize} disabled={loading}>
            {loading ? "Organizing..." : "Create Structured Preview"}
          </button>
        </div>

        {error ? <p className="saved-empty">{error}</p> : null}

        {preview?.chapters?.length ? (
          <section className="saved-library-grid">
            {preview.chapters.map((chapter) => (
              <article key={chapter.chapter_index} className="saved-book-card">
                <h3>{chapter.chapter_title}</h3>
                {chapter.paragraphs.map((paragraph) => (
                  <p key={paragraph.block_id}>{paragraph.text}</p>
                ))}
              </article>
            ))}
          </section>
        ) : null}
      </div>
    </main>
  );
}
