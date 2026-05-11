import React, { useState } from "react";
import { api } from "../api/api";
import { API_BASE_URL } from "../config";
import "../styles/library.css";

export default function LibraryOrganizer() {
  const [title, setTitle] = useState("Untitled");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [planId, setPlanId] = useState(null);
  const [titleEdits, setTitleEdits] = useState({});
  const [splitBoundary, setSplitBoundary] = useState({});
  const [downloadingTxt, setDownloadingTxt] = useState(false);

  function organizerErrorMessage(err, fallback) {
    if (err?.status === 401) return "Please sign in again.";
    if (err?.status === 403) return "Your account does not have access to the Text Book Organizer.";
    if (err?.status === 404) return "Text Book Organizer is unavailable or the requested document was not found.";
    return err?.message || fallback;
  }

  async function handleOrganize() {
    setLoading(true);
    setError("");
    setPreview(null);
    try {
      const ingest = await api("/audiobooks/organizer/ingest-text", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ title, text }),
      });

      const plan = await api("/audiobooks/organizer/propose-plan", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ document_id: ingest.document.id, plan_name: "Default plan" }),
      });

      const phase3Preview = await api("/audiobooks/organizer/preview", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ document_id: ingest.document.id, plan_id: plan.plan_id }),
      });

      setPreview(phase3Preview);
      setDocumentId(ingest.document.id);
      setPlanId(plan.plan_id);
      setTitleEdits({});
      setSplitBoundary({});
    } catch (err) {
      setError(organizerErrorMessage(err, "Organizer request failed."));
    } finally {
      setLoading(false);
    }
  }

  async function applyStructureEdits(payload) {
    if (!documentId || !planId) return;
    setError("");
    try {
      const reviewed = await api("/audiobooks/organizer/review-structure", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ document_id: documentId, plan_id: planId, plan_name: "Reviewed plan", ...payload }),
      });
      const nextPreview = await api("/audiobooks/organizer/preview", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ document_id: documentId, plan_id: reviewed.plan_id }),
      });
      setPlanId(reviewed.plan_id);
      setPreview(nextPreview);
    } catch (err) {
      setError(organizerErrorMessage(err, "Organizer request failed."));
    }
  }

  async function handleDownloadTxt() {
    if (!documentId || !planId) return;
    setDownloadingTxt(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/audiobooks/organizer/export-txt`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId, plan_id: planId }),
      });
      if (!res.ok) {
        let msg = "TXT export failed.";
        try {
          const payload = await res.json();
          msg = payload?.detail ? JSON.stringify(payload.detail) : msg;
        } catch (_err) {
          msg = `TXT export failed (${res.status}).`;
        }
        const error = new Error(msg);
        error.status = res.status;
        throw error;
      }
      const blob = await res.blob();
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
      const filename = match?.[1] || "manuscript.txt";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(organizerErrorMessage(err, "TXT export failed."));
    } finally {
      setDownloadingTxt(false);
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
          <button type="button" className="library-pill" onClick={handleDownloadTxt} disabled={!preview?.chapters?.length || downloadingTxt}>
            {downloadingTxt ? "Downloading TXT..." : "Download TXT"}
          </button>
        </div>

        {error ? <p className="saved-empty">{error}</p> : null}

        {preview?.chapters?.length ? (
          <>
            <section className="saved-book-card">
              <h2>Detected structure preview</h2>
              <p>
                Detected {preview.detected_chapter_count ?? preview.chapters.length} chapters for the book structure preview.
              </p>
              {preview.warnings?.map((warning) => (
                <p key={`${warning.code}-${warning.chapter_count ?? warning.message}`} className="saved-empty">
                  {warning.message}
                </p>
              ))}
              <ol>
                {preview.chapters.map((chapter) => (
                  <li key={`summary-${chapter.chapter_index}`}>
                    {chapter.chapter_title} — {chapter.word_count ?? 0} words
                  </li>
                ))}
              </ol>
            </section>
            <section className="saved-library-grid">
              {preview.chapters.map((chapter) => (
              <article key={chapter.chapter_index} className="saved-book-card">
                <h3>{chapter.chapter_title}</h3>
                <input
                  className="save-input"
                  value={titleEdits[chapter.chapter_index] ?? chapter.chapter_title}
                  onChange={(e) => setTitleEdits((prev) => ({ ...prev, [chapter.chapter_index]: e.target.value }))}
                />
                <div className="library-actions">
                  <button
                    type="button"
                    className="library-pill"
                    onClick={() =>
                      applyStructureEdits({
                        chapter_title_overrides: {
                          [chapter.chapter_index]: titleEdits[chapter.chapter_index] ?? chapter.chapter_title,
                        },
                      })
                    }
                  >
                    Rename title
                  </button>
                  <button type="button" className="library-pill" onClick={() => applyStructureEdits({ merge_chapter_indexes: [chapter.chapter_index] })}>
                    Merge with next
                  </button>
                  <input
                    className="save-input"
                    placeholder="Split at block ID"
                    value={splitBoundary[chapter.chapter_index] ?? ""}
                    onChange={(e) => setSplitBoundary((prev) => ({ ...prev, [chapter.chapter_index]: e.target.value }))}
                  />
                  <button
                    type="button"
                    className="library-pill"
                    onClick={() =>
                      applyStructureEdits({
                        split_operations: [{ chapter_index: chapter.chapter_index, boundary_block_id: splitBoundary[chapter.chapter_index] }],
                      })
                    }
                  >
                    Split chapter
                  </button>
                </div>
                {chapter.paragraphs.map((paragraph) => (
                  <p key={paragraph.block_id}>{paragraph.text}</p>
                ))}
              </article>
              ))}
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}
