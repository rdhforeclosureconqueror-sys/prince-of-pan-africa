import React, { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import JournalSidebar from "../components/JournalSidebar";
import SocialShare from "../components/SocialShare";
import VoiceControls from "../components/VoiceControls";
import { DECLO30 } from "../data/portals/decolo30";
import { sendChatMessage, sendVoiceMessage } from "../api/mufasaClient";

const PORTAL_ID = "DECLO30";

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

function clampText(str, max = 900) {
  if (!str) return "";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

export default function PortalDecolonize() {
  const query = useQuery();

  const initialDay = Math.min(
    Math.max(parseInt(query.get("day") || "1", 10), 1),
    30
  );

  const [day, setDay] = useState(initialDay);

  useEffect(() => {
    setDay(initialDay);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialDay]);

  // ✅ Local lesson from your data file (no API call)
  const lesson = DECLO30.find((d) => d.day === day);

  // ✅ This is what VoiceControls should speak for the LESSON
  const formattedLessonForVoice = useMemo(() => {
    if (!lesson) return "Lesson not found.";
    return (
      `${lesson.title}\n\n` +
      `${lesson.hook}\n\n` +
      `CORE:\n` +
      `L1: ${lesson.core?.L1 || ""}\n\n` +
      `L2: ${lesson.core?.L2 || ""}\n\n` +
      `L3: ${lesson.core?.L3 || ""}\n\n` +
      `PRACTICE: ${lesson.practice || ""}\n\n` +
      `JOURNAL: ${lesson.journal || ""}\n\n` +
      `MINI-Q: ${lesson.miniQ || ""}\n\n` +
      `RESUME_CODE=${lesson.resume || ""}`
    );
  }, [lesson]);

  // ----------------------------
  // ✅ Q&A Thread (New Upgrade)
  // ----------------------------
  const [thread, setThread] = useState([]); // { role: "user"|"assistant", text: string, audio_url?: string|null }
  const [input, setInput] = useState("");
  const [loadingAsk, setLoadingAsk] = useState(false);

  // Optional: clear thread when day changes (clean experience)
  useEffect(() => {
    setThread([]);
    setInput("");
  }, [day]);

  const latestAssistantText = useMemo(() => {
    const last = [...thread].reverse().find((m) => m.role === "assistant");
    return last?.text || "";
  }, [thread]);

  const buildPortalQuestion = (question) => {
    const context = lesson
      ? clampText(
          [
            lesson.title,
            lesson.hook,
            `L1: ${lesson.core?.L1 || ""}`,
            `L2: ${lesson.core?.L2 || ""}`,
            `L3: ${lesson.core?.L3 || ""}`,
            `Practice: ${lesson.practice || ""}`,
            `Journal: ${lesson.journal || ""}`,
            `Mini-Q: ${lesson.miniQ || ""}`,
          ].join("\n\n"),
          900
        )
      : "";

    return [
      `PORTAL_CONTEXT`,
      `portal_id=${PORTAL_ID}`,
      `day=${day}`,
      lesson ? `lesson_context="${context.replace(/"/g, "'")}"` : `lesson_context=""`,
      ``,
      `USER_QUESTION: ${question}`,
      ``,
      `RESPONSE_FORMAT: HOOK + CORE (L1/L2/L3) + PRACTICE + MINI-Q + RESUME_CODE=DECLO30_D{next}`,
    ].join("\n");
  };

  const askText = async () => {
    if (!input.trim() || loadingAsk) return;

    const q = input.trim();
    setThread((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoadingAsk(true);

    try {
      const packed = buildPortalQuestion(q);
      const reply = await sendChatMessage(packed);

      const replyText =
        typeof reply === "string"
          ? reply
          : reply.reply || reply.response || reply.answer || "🦁 Mufasa is silent...";

      setThread((prev) => [
        ...prev,
        { role: "assistant", text: replyText, audio_url: reply?.audio_url || null },
      ]);
    } catch (e) {
      setThread((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Mufasa could not be reached." },
      ]);
    } finally {
      setLoadingAsk(false);
    }
  };

  // ✅ Voice question: record in VoiceControls -> sendVoiceMessage -> get transcript -> ask chat
  const askVoice = async (audioBlob) => {
    if (loadingAsk) return;
    setLoadingAsk(true);

    setThread((prev) => [...prev, { role: "user", text: "🎙️ You spoke..." }]);

    try {
      const data = await sendVoiceMessage(audioBlob);

      const transcript =
        data?.transcript || data?.text || data?.user_text || data?.user || "";

      // Replace placeholder with transcript
      if (transcript) {
        setThread((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i--) {
            if (next[i].role === "user" && next[i].text.includes("You spoke")) {
              next[i] = { role: "user", text: `🎙️ ${transcript}` };
              break;
            }
          }
          return next;
        });
      }

      const packed = buildPortalQuestion(transcript || "Explain this lesson simply.");
      const reply = await sendChatMessage(packed);

      const replyText =
        typeof reply === "string"
          ? reply
          : reply.reply || reply.response || reply.answer || "🦁 Mufasa is silent...";

      setThread((prev) => [
        ...prev,
        { role: "assistant", text: replyText, audio_url: reply?.audio_url || null },
      ]);
    } catch (e) {
      setThread((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Voice Q&A failed to connect." },
      ]);
    } finally {
      setLoadingAsk(false);
    }
  };

  // ✅ Enter-to-send (no shift)
  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askText();
    }
  };

  const copyText = async (txt) => {
    try {
      await navigator.clipboard.writeText(txt);
      alert("Copied ✅");
    } catch {
      alert("Copy failed (browser blocked).");
    }
  };

  const copyAnswer = () => {
    if (!latestAssistantText) return;
    copyText(latestAssistantText);
  };

  const copyQA = () => {
    const lastQ = [...thread].reverse().find((m) => m.role === "user")?.text || "";
    const lastA = latestAssistantText || "";
    if (!lastA) return;
    const pack = `Portal: Decolonize the Mind — Day ${day}\n\nQ: ${lastQ}\n\nA: ${lastA}`;
    copyText(pack);
  };

  return (
    <div className="flex min-h-screen bg-panblack text-white">
      <JournalSidebar />

      <main
        className="flex-1 p-4 md:p-8 overflow-y-auto"
        style={{ maxWidth: 1100, margin: "0 auto", width: "100%" }}
      >
        <h1 className="text-2xl md:text-3xl font-bold text-pangold mb-2">
          Portal: Decolonize the Mind
        </h1>

        <div className="flex flex-wrap items-center gap-3 mb-6">
          <p className="text-gray-400">Day {day} of 30</p>

          <div className="flex gap-2">
            <button
              onClick={() => setDay((d) => Math.max(1, d - 1))}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-[#111] hover:bg-[#1a1a1a]"
            >
              ← Prev
            </button>

            <button
              onClick={() => setDay((d) => Math.min(30, d + 1))}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-[#111] hover:bg-[#1a1a1a]"
            >
              Next →
            </button>
          </div>
        </div>

        {/* ✅ LESSON CARD */}
        {!lesson ? (
          <div className="p-4 border border-gray-700 rounded-lg bg-[#111]">
            ⚠️ Lesson not loaded yet. Add Day {day} into src/data/portals/decolo30.js
          </div>
        ) : (
          <div className="p-4 md:p-6 border border-gray-700 rounded-lg bg-[#111]">
            <h2 className="text-xl md:text-2xl font-bold text-pangold">
              {lesson.title}
            </h2>

            <p className="mt-3 text-gray-200 leading-relaxed">
              <span className="font-bold text-pangold">HOOK: </span>
              {lesson.hook}
            </p>

            <div className="mt-5 space-y-3">
              <div>
                <div className="font-bold text-pangold">CORE (L1/L2/L3)</div>
                <div className="mt-2 space-y-2 text-gray-200 leading-relaxed">
                  <p>
                    <span className="font-bold">L1: </span>
                    {lesson.core?.L1}
                  </p>
                  <p>
                    <span className="font-bold">L2: </span>
                    {lesson.core?.L2}
                  </p>
                  <p>
                    <span className="font-bold">L3: </span>
                    {lesson.core?.L3}
                  </p>
                </div>
              </div>

              <div>
                <div className="font-bold text-pangold">PRACTICE</div>
                <p className="mt-2 text-gray-200 leading-relaxed">
                  {lesson.practice}
                </p>
              </div>

              <div>
                <div className="font-bold text-pangold">JOURNAL PROMPT</div>
                <p className="mt-2 text-gray-200 leading-relaxed">
                  {lesson.journal}
                </p>
              </div>

              <div>
                <div className="font-bold text-pangold">MINI-Q</div>
                <p className="mt-2 text-gray-200 leading-relaxed">{lesson.miniQ}</p>
              </div>

              <div className="mt-4 text-xs text-gray-400">
                RESUME_CODE={lesson.resume}
              </div>
            </div>
          </div>
        )}

        {/* ✅ LESSON VOICE + SHARE */}
        <div className="mt-8">
          {/* IMPORTANT: Your VoiceControls expects latestMessage, not text */}
          <VoiceControls latestMessage={formattedLessonForVoice} />
          <SocialShare />
        </div>

        {/* ✅ Q&A UPGRADE */}
        <div className="mt-8 p-4 md:p-6 border border-gray-700 rounded-lg bg-black/30">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h2 className="text-xl font-bold text-yellow-400">
              Ask Mufasa about this lesson
            </h2>

            <div className="flex gap-2 flex-wrap">
              <button
                onClick={copyAnswer}
                disabled={!latestAssistantText}
                className="px-4 py-2 rounded-lg border border-yellow-700 bg-[#111] hover:bg-[#1a1a1a] disabled:opacity-40"
              >
                Copy Answer
              </button>
              <button
                onClick={copyQA}
                disabled={!latestAssistantText}
                className="px-4 py-2 rounded-lg border border-yellow-700 bg-[#111] hover:bg-[#1a1a1a] disabled:opacity-40"
              >
                Copy Q + A
              </button>
            </div>
          </div>

          {/* Thread */}
          <div className="mt-4 flex flex-col gap-3">
            {thread.map((m, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "92%",
                  padding: "12px 14px",
                  borderRadius: 14,
                  background:
                    m.role === "user" ? "rgba(178,34,34,.9)" : "rgba(0,100,0,.85)",
                  color: "white",
                  whiteSpace: "pre-wrap",
                  overflowWrap: "anywhere",
                }}
              >
                {m.text}
              </div>
            ))}

            {loadingAsk && (
              <div
                style={{
                  alignSelf: "flex-start",
                  maxWidth: "92%",
                  padding: "12px 14px",
                  borderRadius: 14,
                  background: "rgba(0,100,0,.55)",
                  color: "white",
                  fontStyle: "italic",
                }}
              >
                🦁 Mufasa is thinking...
              </div>
            )}
          </div>

          {/* Input */}
          <div className="mt-4 flex flex-col gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Type your question… (Enter to send, Shift+Enter for new line)"
              className="w-full bg-[#111] border border-yellow-600 rounded-lg p-3 text-white"
              style={{ minHeight: 90 }}
            />

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={askText}
                disabled={loadingAsk}
                className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded-lg font-bold disabled:opacity-50"
              >
                {loadingAsk ? "Thinking..." : "Ask"}
              </button>

              {/* Voice question */}
              <div className="flex-1 min-w-[280px]">
                <VoiceControls latestMessage={latestAssistantText} onVoiceSend={askVoice} />
              </div>
            </div>

            {/* Listen to answer */}
            {!!latestAssistantText && (
              <div className="mt-3">
                <div className="text-sm opacity-70 mb-2">
                  Listen to the latest answer:
                </div>
                <VoiceControls latestMessage={latestAssistantText} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
