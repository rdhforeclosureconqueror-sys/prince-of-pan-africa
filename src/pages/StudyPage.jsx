import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/api";

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5, 2];

export default function StudyPage() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [voice, setVoice] = useState("alloy");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [library, setLibrary] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [selectedBook, setSelectedBook] = useState(null);
  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const audioRef = useRef(null);

  const activeChapter = useMemo(() => {
    if (!selectedBook?.chapters?.length) return null;
    return selectedBook.chapters[activeChapterIndex] || null;
  }, [selectedBook, activeChapterIndex]);

  async function loadLibrary() {
    try {
      const response = await api("/audiobooks", { method: "GET" });
      setLibrary(response.items || []);
      if (!selectedBookId && response.items?.length) {
        setSelectedBookId(response.items[0].id);
      }
    } catch (err) {
      setError(err.message || "Failed to load library.");
    }
  }

  async function loadBook(id) {
    if (!id) return;
    try {
      const response = await api(`/audiobooks/${id}`, { method: "GET" });
      setSelectedBook(response);
      const safeChapterIndex = Math.max(0, (response.progress?.chapter_index || 1) - 1);
      setActiveChapterIndex(safeChapterIndex);
      setPlaybackRate(Number(response.progress?.playback_rate || 1));
    } catch (err) {
      setError(err.message || "Failed to load audiobook.");
    }
  }

  useEffect(() => {
    loadLibrary();
  }, []);

  useEffect(() => {
    if (selectedBookId) {
      loadBook(selectedBookId);
    }
  }, [selectedBookId]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate, activeChapter?.audio_url]);

  async function submitGeneration() {
    setError("");
    setStatus("");
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    setIsGenerating(true);
    setStatus("Generating chapters...");

    try {
      let response;
      if (file) {
        const form = new FormData();
        form.append("title", title.trim());
        form.append("author", author.trim() || "Unknown");
        form.append("voice", voice);
        form.append("file", file);
        const apiBase = import.meta.env.VITE_API_BASE_URL || "";
        const res = await fetch(`${apiBase}/audiobooks/upload`, {
          method: "POST",
          credentials: "include",
          body: form,
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.detail || "Upload failed.");
        }
        response = data;
      } else {
        response = await api("/audiobooks/create", {
          method: "POST",
          body: JSON.stringify({
            title: title.trim(),
            author: author.trim() || "Unknown",
            text,
            voice,
          }),
        });
      }

      const cachedLabel = response.cached ? " (cache reused)" : "";
      setStatus(`Audiobook ready${cachedLabel}.`);
      setSelectedBookId(response.audiobook.id);
      await loadLibrary();
    } catch (err) {
      setError(err.message || "Generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function persistProgress() {
    if (!selectedBook) return;
    const currentTime = Math.floor(audioRef.current?.currentTime || 0);
    await api(`/audiobooks/${selectedBook.id}/progress`, {
      method: "POST",
      body: JSON.stringify({
        chapter_index: activeChapterIndex + 1,
        position_seconds: currentTime,
        playback_rate: String(playbackRate),
      }),
    });
  }

  function playNext() {
    if (!selectedBook?.chapters?.length) return;
    setActiveChapterIndex((prev) => Math.min(prev + 1, selectedBook.chapters.length - 1));
  }

  function playPrev() {
    setActiveChapterIndex((prev) => Math.max(prev - 1, 0));
  }

  return (
    <main className="library-shell">
      <div className="library-inner cosmic-readable-shell">
        <h1>Text to Audiobook (V1)</h1>

        <div style={{ display: "grid", gap: 8, marginBottom: 16 }}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Book title" />
          <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Author" />
          <select value={voice} onChange={(e) => setVoice(e.target.value)}>
            <option value="alloy">alloy</option>
            <option value="echo">echo</option>
            <option value="fable">fable</option>
            <option value="onyx">onyx</option>
          </select>
          <textarea
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste text here (or upload .txt)."
          />
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button onClick={submitGeneration} disabled={isGenerating || (!text.trim() && !file)}>
            {isGenerating ? "Generating..." : "Generate Audiobook"}
          </button>
          {status && <p style={{ color: "#c9f7b1" }}>{status}</p>}
          {error && <p style={{ color: "#ff9ea4" }}>{error}</p>}
        </div>

        <section>
          <h2>Saved Library</h2>
          {!library.length && <p>No audiobooks yet.</p>}
          <ul>
            {library.map((book) => (
              <li key={book.id}>
                <button onClick={() => setSelectedBookId(book.id)}>
                  {book.title} — {book.author} ({book.status})
                </button>
              </li>
            ))}
          </ul>
        </section>

        {selectedBook && (
          <section style={{ marginTop: 20 }}>
            <h2>{selectedBook.title}</h2>
            <p>{selectedBook.author}</p>
            <h3>Chapters</h3>
            <ul>
              {selectedBook.chapters.map((chapter, idx) => (
                <li key={chapter.id}>
                  <button onClick={() => setActiveChapterIndex(idx)}>
                    {chapter.title} ({chapter.status})
                  </button>
                </li>
              ))}
            </ul>

            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
              <button onClick={playPrev}>Prev</button>
              <button onClick={() => audioRef.current?.paused ? audioRef.current?.play() : audioRef.current?.pause()}>
                Play/Pause
              </button>
              <button onClick={playNext}>Next</button>
              <label>
                Speed
                <select value={playbackRate} onChange={(e) => setPlaybackRate(Number(e.target.value))}>
                  {SPEED_OPTIONS.map((speed) => (
                    <option value={speed} key={speed}>{speed}x</option>
                  ))}
                </select>
              </label>
            </div>

            {activeChapter?.audio_url ? (
              <audio
                ref={audioRef}
                src={activeChapter.audio_url}
                controls
                onPause={persistProgress}
                onEnded={() => {
                  persistProgress();
                  playNext();
                }}
                style={{ width: "100%", marginTop: 10 }}
              />
            ) : (
              <p>Chapter audio is still generating.</p>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
