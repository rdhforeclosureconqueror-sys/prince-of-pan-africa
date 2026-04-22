import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/api";
import "../styles/studyPage.css";

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5, 2];

function splitIntoSentences(text = "") {
  return text
    .replace(/\s+/g, " ")
    .trim()
    .match(/[^.!?]+[.!?]+|[^.!?]+$/g)
    ?.map((sentence) => sentence.trim())
    .filter(Boolean) || [];
}

function mapSentenceTimings(sentences, duration) {
  if (!sentences.length || !Number.isFinite(duration) || duration <= 0) return [];

  const weightedLength = sentences.map((sentence) => Math.max(sentence.length, 1));
  const totalWeight = weightedLength.reduce((sum, value) => sum + value, 0);

  let elapsed = 0;
  return sentences.map((sentence, index) => {
    const allocation = (weightedLength[index] / totalWeight) * duration;
    const start = elapsed;
    const end = index === sentences.length - 1 ? duration : elapsed + allocation;
    elapsed = end;
    return { sentence, start, end };
  });
}

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
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [showChapterMenu, setShowChapterMenu] = useState(false);
  const [resumePositionSeconds, setResumePositionSeconds] = useState(0);

  const audioRef = useRef(null);
  const sentenceRefs = useRef([]);

  const activeChapter = useMemo(() => {
    if (!selectedBook?.chapters?.length) return null;
    return selectedBook.chapters[activeChapterIndex] || null;
  }, [selectedBook, activeChapterIndex]);

  const chapterSentences = useMemo(() => {
    if (!activeChapter?.text) return [];
    return splitIntoSentences(activeChapter.text);
  }, [activeChapter?.id, activeChapter?.text]);

  const sentenceTimings = useMemo(
    () => mapSentenceTimings(chapterSentences, duration),
    [chapterSentences, duration]
  );

  async function loadLibrary() {
    try {
      const response = await api("/audiobooks", { method: "GET", credentials: "include" });
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
      const response = await api(`/audiobooks/${id}`, { method: "GET", credentials: "include" });
      setSelectedBook(response);
      const safeChapterIndex = Math.max(0, (response.progress?.chapter_index || 1) - 1);
      setActiveChapterIndex(safeChapterIndex);
      setPlaybackRate(Number(response.progress?.playback_rate || 1));
      setResumePositionSeconds(Number(response.progress?.position_seconds || 0));
      setActiveSentenceIndex(0);
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
    if (!audioRef.current) return;
    audioRef.current.playbackRate = playbackRate;
  }, [playbackRate, activeChapter?.audio_url]);

  useEffect(() => {
    sentenceRefs.current = [];
  }, [activeChapter?.id]);

  useEffect(() => {
    if (!audioRef.current || !activeChapter) return;
    audioRef.current.currentTime = 0;
    if (selectedBook?.progress && selectedBook.progress.chapter_index - 1 === activeChapterIndex) {
      audioRef.current.currentTime = resumePositionSeconds;
      setProgress(resumePositionSeconds);
    } else {
      setProgress(0);
    }
  }, [activeChapter?.id, selectedBook?.progress, activeChapterIndex, resumePositionSeconds]);

  useEffect(() => {
    if (!isPlaying) return;
    const activeSentence = sentenceRefs.current[activeSentenceIndex];
    if (!activeSentence) return;
    activeSentence.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeSentenceIndex, isPlaying]);

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
          if (res.status === 401) {
            throw new Error("You must be logged in to use audiobooks.");
          }
          if (res.status === 422) {
            throw new Error("Upload failed. Check file type or missing fields.");
          }
          throw new Error(data?.detail || "Upload failed.");
        }
        response = data;
      } else {
        response = await api("/audiobooks/create", {
          method: "POST",
          credentials: "include",
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
      if (err?.status === 401) {
        setError("You must be logged in to use audiobooks.");
      } else if (err?.status === 422) {
        setError("Upload failed. Check file type or missing fields.");
      } else {
        setError(err.message || "Generation failed.");
      }
    } finally {
      setIsGenerating(false);
    }
  }

  async function persistProgress(positionOverride) {
    if (!selectedBook) return;
    const currentTime = Math.floor((positionOverride ?? audioRef.current?.currentTime) || 0);
    await api(`/audiobooks/${selectedBook.id}/progress`, {
      method: "POST",
      credentials: "include",
      body: JSON.stringify({
        chapter_index: activeChapterIndex + 1,
        position_seconds: currentTime,
        playback_rate: String(playbackRate),
      }),
    });
  }

  async function switchChapter(nextIndex) {
    if (!selectedBook?.chapters?.length) return;
    const boundedIndex = Math.max(0, Math.min(nextIndex, selectedBook.chapters.length - 1));
    await persistProgress();
    setActiveChapterIndex(boundedIndex);
    setActiveSentenceIndex(0);
    setShowChapterMenu(false);
  }

  async function playNext() {
    await switchChapter(activeChapterIndex + 1);
  }

  async function playPrev() {
    await switchChapter(activeChapterIndex - 1);
  }

  function handleTimeUpdate() {
    const currentTime = audioRef.current?.currentTime || 0;
    setProgress(currentTime);

    if (!sentenceTimings.length) {
      if (chapterSentences.length > 1 && duration > 0) {
        const ratioIndex = Math.min(
          chapterSentences.length - 1,
          Math.floor((currentTime / duration) * chapterSentences.length)
        );
        setActiveSentenceIndex(ratioIndex);
      }
      return;
    }

    const newIndex = sentenceTimings.findIndex(({ start, end }) => currentTime >= start && currentTime < end);
    if (newIndex >= 0 && newIndex !== activeSentenceIndex) {
      setActiveSentenceIndex(newIndex);
    }
  }

  async function togglePlayPause() {
    if (!audioRef.current) return;
    if (audioRef.current.paused) {
      await audioRef.current.play();
      setIsPlaying(true);
    } else {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }

  function formatTime(secondsValue) {
    const seconds = Math.max(0, Math.floor(secondsValue || 0));
    const minutes = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const remainder = Math.floor(seconds % 60)
      .toString()
      .padStart(2, "0");
    return `${minutes}:${remainder}`;
  }

  function handleSeek(event) {
    const nextPosition = Number(event.target.value || 0);
    if (!audioRef.current) return;
    audioRef.current.currentTime = nextPosition;
    setProgress(nextPosition);
  }

  return (
    <main className={`study-shell ${isFocusMode ? "is-focus" : ""}`}>
      <div className="study-inner cosmic-readable-shell">
        {!isFocusMode && (
          <>
            <header className="study-header">
              <h1>Text to Audiobook</h1>
              <p>Create, listen, and read in sync with immersive sentence highlighting.</p>
            </header>

            <section className="study-generator">
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
              <input type="file" accept=".txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <button onClick={submitGeneration} disabled={isGenerating || (!text.trim() && !file)}>
                {isGenerating ? "Generating..." : "Generate Audiobook"}
              </button>
              {status && <p className="study-status">{status}</p>}
              {error && <p className="study-error">{error}</p>}
            </section>

            <section className="study-library">
              <h2>Saved Library</h2>
              {!library.length && <p>No audiobooks yet.</p>}
              <ul>
                {library.map((book) => (
                  <li key={book.id}>
                    <button
                      className={selectedBookId === book.id ? "is-active" : ""}
                      onClick={() => setSelectedBookId(book.id)}
                    >
                      {book.title} — {book.author}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}

        {selectedBook && (
          <section className="reader-shell">
            <div className="reader-topbar">
              <div>
                <h2>{selectedBook.title}</h2>
                <p>{selectedBook.author}</p>
              </div>
              <button className="focus-toggle" onClick={() => setIsFocusMode((prev) => !prev)}>
                {isFocusMode ? "Exit Focus" : "Focus Mode"}
              </button>
            </div>

            <div className="reader-grid">
              <aside className="chapter-sidebar">
                <button className="chapter-toggle" onClick={() => setShowChapterMenu((prev) => !prev)}>
                  Chapters ({activeChapterIndex + 1}/{selectedBook.chapters.length})
                </button>
                <ul className={showChapterMenu ? "is-open" : ""}>
                  {selectedBook.chapters.map((chapter, idx) => (
                    <li key={chapter.id}>
                      <button
                        className={idx === activeChapterIndex ? "is-current" : ""}
                        onClick={() => switchChapter(idx)}
                      >
                        {chapter.title}
                      </button>
                    </li>
                  ))}
                </ul>
              </aside>

              <article className="reader-panel" aria-live="polite">
                {chapterSentences.length ? (
                  chapterSentences.map((sentence, idx) => (
                    <span
                      key={`${activeChapter?.id}-${idx}`}
                      ref={(node) => {
                        sentenceRefs.current[idx] = node;
                      }}
                      className={`reader-sentence ${idx === activeSentenceIndex ? "is-highlighted" : ""}`}
                    >
                      {sentence}{" "}
                    </span>
                  ))
                ) : (
                  <p>No chapter text available for reading mode.</p>
                )}
              </article>
            </div>

            <div className="player-shell">
              <div className="player-controls-row">
                <button onClick={playPrev}>Prev</button>
                <button onClick={togglePlayPause}>{isPlaying ? "Pause" : "Play"}</button>
                <button onClick={playNext}>Next</button>
                <label>
                  Speed
                  <select value={playbackRate} onChange={(e) => setPlaybackRate(Number(e.target.value))}>
                    {SPEED_OPTIONS.map((speed) => (
                      <option value={speed} key={speed}>
                        {speed}x
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="progress-shell">
                <span>{formatTime(progress)}</span>
                <input
                  type="range"
                  min={0}
                  max={duration || 0}
                  step={1}
                  value={Math.min(progress, duration || 0)}
                  onChange={handleSeek}
                />
                <span>{formatTime(duration)}</span>
              </div>

              {activeChapter?.audio_url ? (
                <audio
                  ref={audioRef}
                  src={activeChapter.audio_url}
                  preload="metadata"
                  onPlay={() => setIsPlaying(true)}
                  onPause={async () => {
                    setIsPlaying(false);
                    await persistProgress();
                  }}
                  onLoadedMetadata={() => {
                    setDuration(audioRef.current?.duration || 0);
                  }}
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={async () => {
                    await persistProgress(0);
                    if (activeChapterIndex < selectedBook.chapters.length - 1) {
                      await playNext();
                    } else {
                      setIsPlaying(false);
                    }
                  }}
                  style={{ width: "100%" }}
                />
              ) : (
                <p>Chapter audio is still generating.</p>
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
