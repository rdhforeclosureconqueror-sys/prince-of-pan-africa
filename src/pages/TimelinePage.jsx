// src/pages/TimelinePage.jsx
import React, { useMemo, useState } from "react";
import { TIMELINE_EVENTS } from "../data/timelineEvents";

const MUFASA_BASE = "https://mufasa-knowledge-bank.onrender.com";
const TTS_ENDPOINT = `${MUFASA_BASE}/chat/tts`;

export default function TimelinePage() {
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState("");
  const [voiceModel, setVoiceModel] = useState("alloy");
  const [audioUrl, setAudioUrl] = useState(null);

  const events = useMemo(() => TIMELINE_EVENTS, []);

  async function speakAI(text) {
    if (!text?.trim()) return;

    setStatus("Generating AI voice…");
    setAudioUrl(null);

    try {
      const res = await fetch(TTS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice_model: voiceModel }),
      });

      const data = await res.json();
      const raw = data?.audio_url || data?.audioUrl || null;

      if (!raw) {
        setStatus("AI voice failed (no audio_url).");
        return;
      }

      const full = raw.startsWith("http") ? raw : `${MUFASA_BASE}${raw}`;
      setAudioUrl(full);
      setStatus("Ready ✅ Tap play.");
    } catch (e) {
      console.error(e);
      setStatus("AI voice error ❌");
    }
  }

  function openEvent(e) {
    setSelected(e);
    setStatus("");
    setAudioUrl(null);
  }

  function closeModal() {
    setSelected(null);
    setStatus("");
    setAudioUrl(null);
  }

  return (
    <div style={{ padding: 18, color: "#f4f1e8" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h1 style={{ margin: 0, color: "#f5e6b3" }}>Memory Restoration Timeline</h1>
        <p style={{ marginTop: 8, opacity: 0.85 }}>
          Click a point → facts open in a window → Mufasa can read it aloud.
        </p>

        {/* Timeline “points” (simple + reliable first) */}
        <div
          style={{
            marginTop: 16,
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          {events.map((e) => (
            <button
              key={e.id}
              type="button"
              onClick={() => openEvent(e)}
              style={{
                textAlign: "left",
                padding: 14,
                borderRadius: 16,
                border: "1px solid rgba(214,178,94,.35)",
                background: "rgba(0,0,0,.35)",
                color: "#f4f1e8",
                cursor: "pointer",
              }}
            >
              <div style={{ fontSize: 12, color: "rgba(245,230,179,.9)" }}>
                {e.dateLabel}
              </div>
              <div style={{ fontWeight: 800, marginTop: 6 }}>{e.title}</div>
              <div style={{ marginTop: 6, opacity: 0.85, fontSize: 13 }}>
                {e.summary}
              </div>
              <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                {(e.tags || []).slice(0, 3).map((t) => (
                  <span
                    key={t}
                    style={{
                      fontSize: 11,
                      padding: "4px 8px",
                      borderRadius: 999,
                      border: "1px solid rgba(214,178,94,.25)",
                      opacity: 0.9,
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Modal */}
      {selected && (
        <div
          onClick={closeModal}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,.65)",
            display: "grid",
            placeItems: "center",
            padding: 16,
            zIndex: 9999,
          }}
        >
          <div
            onClick={(ev) => ev.stopPropagation()}
            style={{
              width: "min(900px, 96vw)",
              borderRadius: 18,
              border: "1px solid rgba(214,178,94,.35)",
              background: "rgba(10,10,10,.92)",
              padding: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
              <div>
                <div style={{ color: "#f5e6b3", fontSize: 12 }}>
                  {selected.dateLabel} • {selected.id}
                </div>
                <h2 style={{ margin: "6px 0 0" }}>{selected.title}</h2>
              </div>

              <button
                type="button"
                onClick={closeModal}
                style={{
                  height: 40,
                  padding: "0 12px",
                  borderRadius: 12,
                  border: "1px solid rgba(225,29,46,.55)",
                  background: "rgba(0,0,0,.25)",
                  color: "#f4f1e8",
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                ✕ Close
              </button>
            </div>

            <div style={{ marginTop: 12, opacity: 0.9, lineHeight: 1.6 }}>
              <p style={{ marginTop: 0 }}>{selected.summary}</p>
              <p style={{ marginBottom: 0 }}>{selected.details}</p>
            </div>

            {/* AI voice controls */}
            <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
              <select
                value={voiceModel}
                onChange={(e) => setVoiceModel(e.target.value)}
                style={{
                  borderRadius: 999,
                  padding: "10px 12px",
                  border: "1px solid rgba(214,178,94,.45)",
                  background: "rgba(0,0,0,.25)",
                  color: "#f4f1e8",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
                title="AI Voice"
              >
                <option value="alloy">Alloy (Strong)</option>
                <option value="verse">Verse (Smooth)</option>
                <option value="echo">Echo (Narrative)</option>
              </select>

              <button
                type="button"
                onClick={() =>
                  speakAI(
                    `${selected.title}. Date: ${selected.dateLabel}. ${selected.summary} ${selected.details}`
                  )
                }
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  border: "1px solid rgba(16,185,129,.55)",
                  background: "rgba(0,0,0,.25)",
                  color: "#f4f1e8",
                  cursor: "pointer",
                  fontWeight: 800,
                }}
              >
                🔊 Read This
              </button>

              <span style={{ alignSelf: "center", fontSize: 12, opacity: 0.8 }}>
                {status}
              </span>
            </div>

            {audioUrl && (
              <div style={{ marginTop: 12 }}>
                <audio controls preload="auto" style={{ width: "100%" }}>
                  <source src={audioUrl} type="audio/mpeg" />
                  Your browser does not support audio playback.
                </audio>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
