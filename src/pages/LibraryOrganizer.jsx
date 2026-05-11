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
  const [downloadStatus, setDownloadStatus] = useState("");
  const [downloadingExport, setDownloadingExport] = useState("");

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

  async function handleDownloadExport(exportKind, endpoint, fallbackFilename) {
    if (!documentId || !planId) return;
    setDownloadingExport(exportKind);
    setDownloadStatus(`Preparing ${exportKind} export from approved structure...`);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId, plan_id: planId, title, author: "Unknown", language: "en", trim_size: "6x9" }),
      });
      if (!res.ok) {
        let msg = `${exportKind} export failed.`;
        try {
          const payload = await res.json();
          msg = payload?.detail ? JSON.stringify(payload.detail) : msg;
        } catch (_err) {
          msg = `${exportKind} export failed (${res.status}).`;
        }
        const error = new Error(msg);
        error.status = res.status;
        throw error;
      }
      const blob = await res.blob();
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
      const filename = match?.[1] || fallbackFilename;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setDownloadStatus(
        exportKind === "EPUB"
          ? 'EPUB export is ready. On iPhone/iPad, tap Share → Books to open the EPUB.'
          : `${exportKind} export is ready.`
      );
    } catch (err) {
      setError(organizerErrorMessage(err, `${exportKind} export failed.`));
      setDownloadStatus("");
    } finally {
      setDownloadingExport("");
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

        {preview?.chapters?.length ? (
          <section className="saved-book-card">
            <h2>Download publishing exports</h2>
            <p>All downloads are generated from the same approved canonical book structure. No audio, audiobook, MP3, M4B, or TTS output is created here.</p>
            <div className="library-actions">
              <button type="button" className="library-pill" onClick={() => handleDownloadExport("DOCX", "/audiobooks/organizer/export-docx", "manuscript.docx")} disabled={!!downloadingExport}>
                {downloadingExport === "DOCX" ? "Preparing DOCX..." : "Download DOCX"}
              </button>
              <span className="saved-book-meta">Editable manuscript for author/editor revisions.</span>
              <button type="button" className="library-pill" onClick={() => handleDownloadExport("EPUB", "/audiobooks/organizer/export-epub", "manuscript.epub")} disabled={!!downloadingExport}>
                {downloadingExport === "EPUB" ? "Preparing EPUB..." : "Download EPUB"}
              </button>
              <span className="saved-book-meta">Ebook with reflowable chapters and clickable navigation. On iPhone/iPad, tap Share → Books to open the EPUB.</span>
              <button type="button" className="library-pill" onClick={() => handleDownloadExport("Print PDF", "/audiobooks/organizer/export-print-pdf", "manuscript-print-interior.pdf")} disabled={!!downloadingExport}>
                {downloadingExport === "Print PDF" ? "Preparing Print PDF..." : "Download Print PDF"}
              </button>
              <span className="saved-book-meta">Physical book / paperback interior PDF, default 6×9 inches.</span>
              <button type="button" className="library-pill" onClick={() => handleDownloadExport("TXT/Markdown", "/audiobooks/organizer/export-txt", "manuscript.txt")} disabled={!!downloadingExport}>
                {downloadingExport === "TXT/Markdown" ? "Preparing TXT..." : "Download TXT/Markdown"}
              </button>
              <span className="saved-book-meta">Plain text backup only; no page formatting expectations.</span>
            </div>
            {downloadStatus ? <p className="saved-empty">{downloadStatus}</p> : null}
          </section>
        ) : null}

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
