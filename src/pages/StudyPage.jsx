import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/api";
import { API_BASE_URL } from "../config";
import "../styles/studyPage.css";

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5, 2];
const ACCESS_OPTIONS = ["free", "member", "subscriber", "purchased"];

function splitIntoSentences(text = "") {
  return (
    text
      .replace(/\s+/g, " ")
      .trim()
      .match(/[^.!?]+[.!?]+|[^.!?]+$/g)
      ?.map((sentence) => sentence.trim())
      .filter(Boolean) || []
  );
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
  const location = useLocation();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [voice, setVoice] = useState("alloy");
  const [accessLevel, setAccessLevel] = useState("free");
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
  const [completedChapters, setCompletedChapters] = useState([]);
  const [reflections, setReflections] = useState([]);
  const [showReflectionPrompt, setShowReflectionPrompt] = useState(false);
  const [reflectionNote, setReflectionNote] = useState("");
  const [reflectionPrompt, setReflectionPrompt] = useState("");
  const [reflectionSummary, setReflectionSummary] = useState("");

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

  const sentenceTimings = useMemo(() => mapSentenceTimings(chapterSentences, duration), [chapterSentences, duration]);

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
      setCompletedChapters(response.progress?.completed_chapters || []);
      setActiveSentenceIndex(0);

      const reflectionRes = await api(`/audiobooks/${id}/reflections`, { method: "GET", credentials: "include" });
      setReflections(reflectionRes.items || []);
      setReflectionSummary("");
    } catch (err) {
      setError(err.message || "Failed to load audiobook.");
    }
  }

  useEffect(() => {
    loadLibrary();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const preselectId = Number(params.get("book") || 0);
    if (preselectId > 0) setSelectedBookId(preselectId);
  }, [location.search]);

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
    activeSentence.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  }, [activeSentenceIndex, isPlaying]);

  async function submitGeneration({ generateAudio }) {
    setError("");
    setStatus("");
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }

    setIsGenerating(true);
    setStatus(generateAudio ? "Generating chapters and audio..." : "Saving draft into your library...");

    try {
      let response;
      if (file) {
        const form = new FormData();
        form.append("title", title.trim());
        form.append("author", author.trim() || "Unknown");
        form.append("voice", voice);
        form.append("file", file);
        form.append("generate_audio", generateAudio ? "true" : "false");
        form.append("access_level", accessLevel);
        const res = await fetch(`${API_BASE_URL}/audiobooks/upload`, {
          method: "POST",
          credentials: "include",
          body: form,
        });
        const data = await res.json();
        if (!res.ok) {
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
            generate_audio: generateAudio,
            access_level: accessLevel,
          }),
        });
      }

      const cachedLabel = response.cached ? " (cache reused)" : "";
      setStatus(generateAudio ? `Audiobook ready${cachedLabel}.` : `Book draft saved${cachedLabel}.`);
      setSelectedBookId(response.audiobook.id);
      navigate(`/study?book=${response.audiobook.id}`, { replace: true });
      await loadLibrary();
    } catch (err) {
      if (err?.status === 422) {
        setError("Upload failed. Check file type or missing fields.");
      } else {
        setError(err.message || "Save/generation failed.");
      }
    } finally {
      setIsGenerating(false);
    }
  }

  async function generateAudioForSavedBook() {
    if (!selectedBook?.id) return;
    setStatus("Generating chapter audio for this saved book...");
    setError("");
    try {
      const response = await api(`/audiobooks/${selectedBook.id}/generate-audio`, { method: "POST" });
      setStatus(`Audio generation status: ${response.status}`);
      await loadBook(selectedBook.id);
      await loadLibrary();
    } catch (err) {
      setError(err.message || "Failed to generate audio.");
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
        completed_chapters: completedChapters,
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

  function chapterReflectionByIndex(chapterIndex) {
    return reflections.find((item) => item.chapter_index === chapterIndex) || null;
  }

  async function completeCurrentChapterAndPrompt() {
    const chapterNumber = activeChapterIndex + 1;
    const nextCompleted = Array.from(new Set([...completedChapters, chapterNumber])).sort((a, b) => a - b);
    setCompletedChapters(nextCompleted);

    const basePrompt = `After Chapter ${chapterNumber} (${activeChapter?.title || `Chapter ${chapterNumber}`}), what one idea felt most transformative, and how will you apply it this week?`;
    setReflectionPrompt(basePrompt);
    setReflectionNote(chapterReflectionByIndex(chapterNumber)?.notes || "");
    setShowReflectionPrompt(true);

    await api(`/audiobooks/${selectedBook.id}/progress`, {
      method: "POST",
      credentials: "include",
      body: JSON.stringify({
        chapter_index: chapterNumber,
        position_seconds: 0,
        playback_rate: String(playbackRate),
        completed_chapters: nextCompleted,
      }),
    });
  }

  async function saveReflection({ skipped }) {
    if (!selectedBook?.id) return;
    const chapterNumber = activeChapterIndex + 1;
    const payload = { notes: skipped ? "" : reflectionNote, skipped };
    const res = await api(`/audiobooks/${selectedBook.id}/chapters/${chapterNumber}/reflection`, {
      method: "PUT",
      credentials: "include",
      body: JSON.stringify(payload),
    });
    const updated = {
      chapter_index: chapterNumber,
      prompt: res.prompt || reflectionPrompt,
      notes: payload.notes,
      skipped,
      updated_at: new Date().toISOString(),
    };
    setReflections((prev) => {
      const filtered = prev.filter((item) => item.chapter_index !== chapterNumber);
      return [...filtered, updated].sort((a, b) => a.chapter_index - b.chapter_index);
    });
    setShowReflectionPrompt(false);
  }

  async function generateReflectionSummary() {
    if (!selectedBook?.id) return;
    const res = await api(`/audiobooks/${selectedBook.id}/reflections/summary`, {
      method: "POST",
      credentials: "include",
      body: JSON.stringify({ include_skipped: false }),
    });
    setReflectionSummary(res.summary || "");
  }

  function handleTimeUpdate() {
    const currentTime = audioRef.current?.currentTime || 0;
    setProgress(currentTime);

    if (!sentenceTimings.length) {
      if (chapterSentences.length > 1 && duration > 0) {
        const ratioIndex = Math.min(chapterSentences.length - 1, Math.floor((currentTime / duration) * chapterSentences.length));
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

  function seekToSentence(index) {
    if (!audioRef.current || !sentenceTimings[index]) return;
    const nextStart = sentenceTimings[index].start;
    audioRef.current.currentTime = nextStart;
    setProgress(nextStart);
    setActiveSentenceIndex(index);
  }

  function formatTime(secondsValue) {
    const seconds = Math.max(0, Math.floor(secondsValue || 0));
    const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
    const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
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
              <h1>Audiobook Studio + Library</h1>
              <p>Save full manuscripts, auto-segment into chapters, generate chapter audio when ready, and read/listen in sync with sentence tracking.</p>
            </header>

            <section className="study-generator">
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Book title" />
              <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Author" />
              <div className="generator-grid-row">
                <select value={voice} onChange={(e) => setVoice(e.target.value)}>
                  <option value="alloy">alloy</option>
                  <option value="echo">echo</option>
                  <option value="fable">fable</option>
                  <option value="onyx">onyx</option>
                </select>
                <select value={accessLevel} onChange={(e) => setAccessLevel(e.target.value)}>
                  {ACCESS_OPTIONS.map((option) => (
                    <option value={option} key={option}>
                      Access: {option}
                    </option>
                  ))}
                </select>
              </div>
              <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste text here (or upload .txt)." />
              <input type="file" accept=".txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <div className="generator-cta-row">
                <button onClick={() => submitGeneration({ generateAudio: false })} disabled={isGenerating || (!text.trim() && !file)}>
                  {isGenerating ? "Saving..." : "Save Draft Book"}
                </button>
                <button onClick={() => submitGeneration({ generateAudio: true })} disabled={isGenerating || (!text.trim() && !file)}>
                  {isGenerating ? "Generating..." : "Generate Audiobook"}
                </button>
              </div>
              {status && <p className="study-status">{status}</p>}
              {error && <p className="study-error">{error}</p>}
            </section>

            <section className="study-library">
              <h2>Saved Library</h2>
              {!library.length && <p>No saved books yet.</p>}
              <ul>
                {library.map((book) => (
                  <li key={book.id}>
                    <button className={selectedBookId === book.id ? "is-active" : ""} onClick={() => setSelectedBookId(book.id)}>
                      <strong>{book.title}</strong> — {book.author}
                      <span>
                        {book.status} • {book.access_level} • {book.audio_chapter_count}/{book.chapter_count} chapters voiced
                      </span>
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
                <p>
                  {selectedBook.author} • {selectedBook.status} • access: {selectedBook.access_level} • {selectedBook.segmentation_strategy}
                </p>
              </div>
              <div className="reader-actions">
                {selectedBook.audio_chapter_count < selectedBook.chapter_count && (
                  <button className="focus-toggle" onClick={generateAudioForSavedBook}>
                    Generate Missing Audio
                  </button>
                )}
                <button className="focus-toggle" onClick={() => setIsFocusMode((prev) => !prev)}>
                  {isFocusMode ? "Exit Focus" : "Focus Mode"}
                </button>
              </div>
            </div>

            <div className="reader-grid">
              <aside className="chapter-sidebar">
                <button className="chapter-toggle" onClick={() => setShowChapterMenu((prev) => !prev)}>
                  Chapters ({activeChapterIndex + 1}/{selectedBook.chapters.length})
                </button>
                <ul className={showChapterMenu ? "is-open" : ""}>
                  {selectedBook.chapters.map((chapter, idx) => (
                    <li key={chapter.id}>
                      <button className={idx === activeChapterIndex ? "is-current" : ""} onClick={() => switchChapter(idx)}>
                        {chapter.title}
                        <small>{chapter.status} {completedChapters.includes(idx + 1) ? "• completed" : ""}</small>
                      </button>
                    </li>
                  ))}
                </ul>
              </aside>

              <article className="reader-panel" aria-live="polite">
                <p className="reader-context">Sentence {activeSentenceIndex + 1} of {Math.max(chapterSentences.length, 1)}</p>
                {chapterSentences.length ? (
                  chapterSentences.map((sentence, idx) => (
                    <button
                      type="button"
                      key={`${activeChapter?.id}-${idx}`}
                      ref={(node) => {
                        sentenceRefs.current[idx] = node;
                      }}
                      className={`reader-sentence ${idx === activeSentenceIndex ? "is-highlighted" : ""}`}
                      onClick={() => seekToSentence(idx)}
                    >
                      {sentence}
                    </button>
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
                <button onClick={completeCurrentChapterAndPrompt}>Complete Chapter</button>
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
                <input type="range" min={0} max={duration || 0} step={1} value={Math.min(progress, duration || 0)} onChange={handleSeek} />
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
                    await completeCurrentChapterAndPrompt();
                    setIsPlaying(false);
                  }}
                  style={{ width: "100%" }}
                />
              ) : (
                <p>Chapter audio is not generated yet. Use “Generate Missing Audio”.</p>
              )}
            </div>

            {showReflectionPrompt && (
              <section className="reflection-shell">
                <h3>Chapter Reflection</h3>
                <p>{reflectionPrompt}</p>
                <textarea
                  rows={5}
                  value={reflectionNote}
                  onChange={(e) => setReflectionNote(e.target.value)}
                  placeholder="Write your notes for this chapter..."
                />
                <div className="reflection-actions">
                  <button onClick={() => saveReflection({ skipped: false })}>Save Reflection</button>
                  <button onClick={() => saveReflection({ skipped: true })}>Skip</button>
                </div>
              </section>
            )}

            <section className="reflection-history">
              <div className="reflection-history-header">
                <h3>Chapter Reflections</h3>
                <button onClick={generateReflectionSummary}>Generate Combined Summary</button>
              </div>
              {!reflections.length ? (
                <p>No reflections saved yet.</p>
              ) : (
                <ul>
                  {reflections.map((item) => (
                    <li key={`reflection-${item.chapter_index}`}>
                      <strong>Chapter {item.chapter_index}</strong>
                      <p>{item.skipped ? "Skipped reflection." : item.notes || "No notes."}</p>
                    </li>
                  ))}
                </ul>
              )}
              {reflectionSummary && <pre className="reflection-summary">{reflectionSummary}</pre>}
            </section>
          </section>
        )}
      </div>
    </main>
  );
}
