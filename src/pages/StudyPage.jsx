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

function absoluteApiUrl(path) {
  if (!path) return "";
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}

function filenameFromContentDisposition(header, fallback = "chapter-audio.mp3") {
  if (!header) return fallback;
  const utf8Match = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1].replace(/["']/g, ""));
  const quotedMatch = header.match(/filename="([^\"]+)"/i);
  if (quotedMatch?.[1]) return quotedMatch[1];
  const bareMatch = header.match(/filename=([^;]+)/i);
  return bareMatch?.[1]?.trim() || fallback;
}

async function readDownloadError(response) {
  const contentType = response.headers.get("content-type") || "";
  let detail = "";
  if (contentType.includes("application/json")) {
    const data = await response.json();
    detail = data?.detail || data?.error || "";
  } else {
    detail = await response.text();
  }

  if (response.status === 401 || response.status === 403) {
    return "Audio download is not authorized. Please sign in with access to this audiobook.";
  }
  if (response.status === 404) {
    return detail || "Audio file is missing from storage. Please regenerate this chapter.";
  }
  if (response.status === 409) {
    return detail || "Audio generation is not complete for this chapter yet.";
  }
  return detail || "Audio download failed.";
}

function isMissingSavedChapterAudioError(err) {
  const detail = err?.payload?.detail || err?.message || "";
  return err?.status === 404 && detail.includes("No saved audio found for this chapter.");
}

function generatedAudioUrlFromResponse(response) {
  const raw = response?.audio_url || response?.audioUrl || "";
  return absoluteApiUrl(raw);
}

function logChapterAudioFlow(flow, details = {}) {
  console.info("[StudyPage] chapter audio flow", { flow, ...details });
}

function isGenerationTerminal(progressState) {
  return ["complete", "failed", "partially_complete"].includes(progressState?.status);
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
  const [generationProgress, setGenerationProgress] = useState(null);
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
  const [savedAudioNotice, setSavedAudioNotice] = useState("");

  const audioRef = useRef(null);
  const sentenceRefs = useRef([]);

  const activeChapter = useMemo(() => {
    if (!selectedBook?.chapters?.length) return null;
    return selectedBook.chapters[activeChapterIndex] || null;
  }, [selectedBook, activeChapterIndex]);

  const activeSavedAudio = activeChapter?.saved_audio || null;

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
      setGenerationProgress(response.generation_progress || null);
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
    if (!selectedBook?.id) return undefined;
    const activeStatuses = new Set(["pending", "chunking", "generating_chapters"]);
    if (!activeStatuses.has(selectedBook.status)) return undefined;

    let cancelled = false;
    let inFlight = false;
    let timer = null;

    const scheduleNextPoll = () => {
      if (!cancelled) {
        timer = window.setTimeout(pollGenerationStatus, 3000);
      }
    };

    const pollGenerationStatus = async () => {
      if (cancelled || inFlight) return;
      inFlight = true;
      try {
        const response = await api(`/audiobooks/${selectedBook.id}/generation-status`, { method: "GET", credentials: "include" });
        const nextProgress = response.generation_progress || null;
        if (cancelled) return;

        setGenerationProgress(nextProgress);
        if (isGenerationTerminal(nextProgress)) {
          await loadBook(selectedBook.id);
          await loadLibrary();
          return;
        }

        scheduleNextPoll();
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError.message || "Unable to poll generation progress.");
          scheduleNextPoll();
        }
      } finally {
        inFlight = false;
      }
    };

    pollGenerationStatus();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [selectedBook?.id, selectedBook?.status]);

  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.playbackRate = playbackRate;
  }, [playbackRate, activeChapter?.audio_url]);

  useEffect(() => {
    sentenceRefs.current = [];
  }, [activeChapter?.id]);

  useEffect(() => {
    if (!selectedBook?.id || !activeChapter?.id) return;
    let cancelled = false;
    async function loadSavedAudioMetadata() {
      try {
        logChapterAudioFlow("saved chapter audio metadata lookup", {
          bookId: selectedBook.id,
          chapterId: activeChapter.id,
          chapterIndex: activeChapter.chapter_index,
        });
        const response = await api(`/api/audio/book/${selectedBook.id}/chapter/${activeChapter.id}`, { method: "GET", credentials: "include" });
        if (cancelled || !response?.audio) return;
        setSavedAudioNotice(response.message || "Saved audio already exists. Use saved audio or regenerate?");
        setSelectedBook((prev) => {
          if (!prev?.chapters) return prev;
          return {
            ...prev,
            chapters: prev.chapters.map((chapter) =>
              chapter.id === activeChapter.id
                ? { ...chapter, audio_url: response.audio.audioUrl || chapter.audio_url, saved_audio: response.audio, audio_asset_id: response.audio.id }
                : chapter,
            ),
          };
        });
      } catch (err) {
        if (err.status !== 404) setError(err.message || "No saved audio found for this chapter.");
        if (!cancelled && err.status === 404) setSavedAudioNotice("");
      }
    }
    loadSavedAudioMetadata();
    return () => {
      cancelled = true;
    };
  }, [selectedBook?.id, activeChapter?.id]);

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
    setStatus(generateAudio ? "Job queued. Preparing chapter generation..." : "Saving draft into your library...");

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
      setStatus(generateAudio ? `Generation started${cachedLabel}.` : `Book draft saved${cachedLabel}.`);
      setSelectedBookId(response.audiobook.id);
      navigate(`/study?book=${response.audiobook.id}`, { replace: true });
      await loadLibrary();
    } catch (err) {
      setError(err.message || "Save/generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function generateAudioForSavedBook() {
    if (!selectedBook?.id) return;
    setStatus("Queued generation for missing chapter audio...");
    setError("");
    try {
      const response = await api(`/audiobooks/${selectedBook.id}/generate-audio`, { method: "POST" });
      setStatus(`Audio generation status: ${response.status}. Track progress below.`);
      await loadBook(selectedBook.id);
      await loadLibrary();
    } catch (err) {
      setError(err.message || "Failed to generate audio.");
    }
  }

  async function generateActiveChapterAudio({ regenerate = false } = {}) {
    if (!selectedBook?.id || !activeChapter?.chapter_index) return;
    if (activeSavedAudio && !regenerate) {
      setStatus("Saved audio already exists. Use saved audio or regenerate? Defaulting to saved audio.");
      await useSavedAudio();
      return;
    }
    if (regenerate && !window.confirm("Regenerating may use a new AI voice request. Continue?")) return;
    setStatus(`${regenerate ? "Regenerating" : "Generating"} chapter ${activeChapter.chapter_index}...`);
    setError("");
    try {
      const suffix = regenerate ? "?regenerate=true" : "";
      const response = await api(`/audiobooks/${selectedBook.id}/chapters/${activeChapter.chapter_index}/generate${suffix}`, { method: "POST", credentials: "include" });
      setStatus(response.message || `Chapter ${activeChapter.chapter_index} ${regenerate ? "regenerated" : "generated"}.`);
      await loadBook(selectedBook.id);
      await loadLibrary();
    } catch (err) {
      setError(err.message || "Failed to generate this chapter.");
    }
  }

  async function generateSkillWorldChapterAudio() {
    if (!selectedBook?.id || !activeChapter?.id) return "";
    const chapterText = (activeChapter.text || "").trim();
    if (!chapterText) {
      throw new Error("No chapter text is available for generated voice.");
    }

    const chapterVoice = selectedBook.voice || voice || "alloy";
    logChapterAudioFlow("generated Skill World TTS flow", {
      bookId: selectedBook.id,
      chapterId: activeChapter.id,
      chapterIndex: activeChapter.chapter_index,
      voice: chapterVoice,
    });
    setStatus("No saved chapter audio found. Generating Skill World voice...");

    const response = await api("/api/skill-world/audio", {
      method: "POST",
      credentials: "include",
      body: JSON.stringify({
        text: chapterText,
        voice_model: chapterVoice,
        voice: chapterVoice,
        format: "mp3",
        speed: playbackRate,
        pitch: 1,
      }),
    });
    const audioUrl = generatedAudioUrlFromResponse(response);
    if (!audioUrl) {
      throw new Error("Generated Skill World TTS response did not include audio_url.");
    }

    setSelectedBook((prev) => ({
      ...prev,
      chapters: prev.chapters.map((chapter) =>
        chapter.id === activeChapter.id
          ? { ...chapter, audio_url: audioUrl, generated_audio: { audio_url: audioUrl, cached: Boolean(response.cached) }, status: "completed" }
          : chapter,
      ),
    }));
    setStatus(`Generated Skill World voice${response.cached ? " from cache" : ""}.`);
    return audioUrl;
  }

  async function useSavedAudio() {
    if (!selectedBook?.id || !activeChapter?.id) return "";
    setError("");
    logChapterAudioFlow("saved chapter audio flow", {
      bookId: selectedBook.id,
      chapterId: activeChapter.id,
      chapterIndex: activeChapter.chapter_index,
    });
    try {
      const response = await api(`/api/audio/book/${selectedBook.id}/chapter/${activeChapter.id}`, { method: "GET", credentials: "include" });
      const audioUrl = response.audio.audioUrl || response.audio.audio_url || "";
      setSelectedBook((prev) => ({
        ...prev,
        chapters: prev.chapters.map((chapter) =>
          chapter.id === activeChapter.id
            ? { ...chapter, audio_url: audioUrl, saved_audio: response.audio, audio_asset_id: response.audio.id, status: "completed" }
            : chapter,
        ),
      }));
      setStatus("Using saved audio. AI voice provider was not called.");
      return audioUrl;
    } catch (err) {
      if (isMissingSavedChapterAudioError(err)) {
        try {
          return await generateSkillWorldChapterAudio();
        } catch (generationErr) {
          setError(generationErr.message || "Generated Skill World voice failed.");
          return "";
        }
      }
      setError(err.message || "No saved audio found for this chapter.");
      return "";
    }
  }

  async function saveActiveAudio() {
    if (!selectedBook?.id || !activeChapter?.id || !activeChapter?.audio_url) return;
    setError("");
    try {
      const response = await api("/api/audio/save", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          bookId: selectedBook.id,
          chapterId: activeChapter.id,
          title: activeChapter.title,
          voice: selectedBook.voice,
          model: selectedBook.voice,
          duration: Math.floor(duration || 0),
          format: "mp3",
          audioUrl: activeChapter.audio_url,
        }),
      });
      setSelectedBook((prev) => ({
        ...prev,
        chapters: prev.chapters.map((chapter) =>
          chapter.id === activeChapter.id ? { ...chapter, saved_audio: response.audio, audio_asset_id: response.audio.id } : chapter,
        ),
      }));
      setStatus("Audio saved. Download is now available.");
    } catch (err) {
      setError(err.message || "Audio save failed. Please try again.");
    }
  }

  async function playSavedAudio() {
    try {
      const audioUrl = await useSavedAudio();
      if (!audioUrl) return;
      window.setTimeout(async () => {
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          await audioRef.current.play();
          setIsPlaying(true);
        }
      }, 0);
    } catch (err) {
      setError(err.message || "Unable to play chapter audio.");
    }
  }

  async function downloadSavedAudio() {
    if (!activeSavedAudio?.downloadUrl) {
      setError("Audio download failed. Please try again.");
      return;
    }

    setError("");
    setStatus("Preparing audio download...");
    try {
      const response = await fetch(absoluteApiUrl(activeSavedAudio.downloadUrl), {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(await readDownloadError(response));
      }

      const contentType = response.headers.get("content-type") || "";
      if (!contentType.startsWith("audio/")) {
        throw new Error("Audio download failed: server did not return an audio file.");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filenameFromContentDisposition(
        response.headers.get("content-disposition"),
        activeSavedAudio.filename || "chapter-audio.mp3",
      );
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus("Audio download started.");
    } catch (err) {
      setError(err.message || "Audio download failed. Please try again.");
      setStatus("");
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
    try {
      if (!activeChapter?.audio_url) {
        await playSavedAudio();
        return;
      }
      if (!audioRef.current) return;
      if (audioRef.current.paused) {
        await audioRef.current.play();
        setIsPlaying(true);
      } else {
        audioRef.current.pause();
        setIsPlaying(false);
      }
    } catch (err) {
      setError(err.message || "Unable to play chapter audio.");
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

  function statusLabelFromProgress(progressState) {
    if (!progressState) return "";
    if (progressState.status === "pending") return "Pending";
    if (progressState.status === "chunking") return "Chunking";
    if (progressState.status === "generating_chapters") return "Generating chapters";
    if (progressState.status === "partially_complete") return "Completed with errors";
    if (progressState.status === "complete") return "Complete";
    if (progressState.status === "failed") return "Failed";
    return progressState.status;
  }

  function generationErrorSummary(progressState) {
    const errors = progressState?.failed_chapter_errors || [];
    if (!errors.length) return "";
    return errors
      .slice(0, 3)
      .map((item) => `Chapter ${item.chapter_index}: ${item.message}`)
      .join(" • ");
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
              <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste text here (or upload .txt/.pdf)." />
              <input type="file" accept=".txt,.pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <p className="study-status">Supported upload types: .txt, .pdf</p>
              <div className="generator-cta-row">
                <button onClick={() => submitGeneration({ generateAudio: false })} disabled={isGenerating || (!text.trim() && !file)}>
                  {isGenerating ? "Saving..." : "Save Draft Book"}
                </button>
                <button onClick={() => submitGeneration({ generateAudio: true })} disabled={isGenerating || (!text.trim() && !file)}>
                  {isGenerating ? "Generating..." : "Generate Audiobook"}
                </button>
              </div>
              {status && <p className="study-status">{status}</p>}
              {generationProgress && (
                <p className="study-status">
                  {statusLabelFromProgress(generationProgress)} • {generationProgress.completed_chapters}/{generationProgress.total_chapters} chapters complete
                  {generationProgress.current_chapter_index ? ` • Generating chapter ${generationProgress.current_chapter_index} of ${generationProgress.total_chapters}` : ""}
                  {generationProgress.failed_chapters ? ` • ${generationProgress.failed_chapters} failed` : ""}
                  {generationErrorSummary(generationProgress) ? ` • ${generationErrorSummary(generationProgress)}` : ""}
                </p>
              )}
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
                {generationProgress && (
                  <p>
                    {statusLabelFromProgress(generationProgress)} — {generationProgress.completed_chapters}/{generationProgress.total_chapters} complete
                    {generationProgress.current_chapter_index ? ` — Generating chapter ${generationProgress.current_chapter_index} of ${generationProgress.total_chapters}` : ""}
                    {generationProgress.message ? ` — ${generationProgress.message}` : ""}
                    {generationErrorSummary(generationProgress) ? ` — ${generationErrorSummary(generationProgress)}` : ""}
                  </p>
                )}
              </div>
              <div className="reader-actions">
                {selectedBook.audio_chapter_count < selectedBook.chapter_count && (
                  <button className="focus-toggle" onClick={generateAudioForSavedBook}>
                    Generate Missing Audio
                  </button>
                )}
                {!activeChapter?.audio_url && (
                  <button className="focus-toggle" onClick={() => generateActiveChapterAudio()}>
                    Generate Next Chapter
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
                {activeSavedAudio && <button onClick={useSavedAudio}>Use Saved Audio</button>}
                {activeSavedAudio && <button onClick={playSavedAudio}>Play Saved Audio</button>}
                {activeChapter?.audio_url && !activeSavedAudio && <button onClick={saveActiveAudio}>Save Audio</button>}
                {activeSavedAudio && <button onClick={downloadSavedAudio}>Download Audio</button>}
                <button onClick={() => generateActiveChapterAudio({ regenerate: true })}>Regenerate Audio</button>
              </div>
              {savedAudioNotice && activeSavedAudio && <p className="study-status">{savedAudioNotice}</p>}
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

              <audio
                ref={audioRef}
                src={activeChapter?.audio_url || undefined}
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
              {!activeChapter?.audio_url && <p>Chapter audio is not saved yet. Press Play to generate Skill World voice.</p>}
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
