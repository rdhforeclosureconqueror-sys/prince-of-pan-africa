import { useState, useEffect, useRef } from "react";
import VoiceControls from "../components/VoiceControls";
import JournalSidebar from "../components/JournalSidebar";
import "../styles/theme.css";
import { sendChatMessage, sendVoiceMessage } from "../api/mufasaClient";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ✅ Text chat
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendChatMessage(input);

      const replyText =
        typeof reply === "string"
          ? reply
          : reply.reply || reply.response || reply.answer || "🦁 Mufasa is silent...";

      const aiMessage = {
        role: "assistant",
        text: replyText,
        audio_url: reply?.audio_url || null,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Mufasa could not be reached." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Enter to send (no shift)
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ✅ Voice input (Fixed)
  const handleVoiceInput = async (audioBlob) => {
    if (loading) return;
    setLoading(true);

    // Placeholder user message
    setMessages((prev) => [
      ...prev,
      { role: "user", text: "🎙️ You spoke to Mufasa..." },
    ]);

    try {
      const data = await sendVoiceMessage(audioBlob);

      // Transcript field variations
      const transcript =
        data?.transcript || data?.text || data?.user_text || data?.user || null;

      // Reply field variations
      const replyText =
        data?.reply ||
        data?.response ||
        data?.answer ||
        data?.message ||
        (typeof data === "string" ? data : "") ||
        "🦁 Mufasa is silent...";

      // Replace placeholder with transcript if present
      if (transcript) {
        setMessages((prev) => {
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

      // Normalize audio_url
      const baseURL = "https://mufasa-knowledge-bank.onrender.com";
      const rawAudio = data?.audio_url || data?.audioUrl || null;

      const fullAudioUrl = rawAudio
        ? rawAudio.startsWith("http")
          ? rawAudio
          : `${baseURL}${rawAudio}`
        : null;

      const aiMessage = {
        role: "assistant",
        text: replyText,
        audio_url: fullAudioUrl,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error("Voice chat failed:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Voice chat failed to connect." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Latest AI text for VoiceControls TTS
  const latestReply =
    messages.filter((msg) => msg.role === "assistant").slice(-1)[0]?.text || "";

  // ✅ Language page links (served from /public/languages/)
  const openSwahili = () => window.open("/languages/swahili.html", "_self");
  const openYoruba = () => window.open("/languages/yoruba.html", "_self");

  return (
    <div className="app-container">
      <JournalSidebar />

      <main className="chat-area">
        {/* Header */}
        <div className="chat-header">
          <h1 className="title">Mufasa The Decolonizer</h1>

          <p className="subtitle">
            Black History 365. Powered by{" "}
            <span className="mufasa">Maat</span>.
          </p>

          {/* ✅ Languages */}
          <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={openSwahili}
              className="send-btn"
              style={{
                padding: "10px 14px",
                borderRadius: 14,
                border: "1px solid rgba(214,178,94,.55)",
                background: "rgba(0,0,0,.35)",
                color: "#f5e6b3",
                cursor: "pointer",
              }}
            >
              🌍 Swahili Lessons
            </button>

            <button
              type="button"
              onClick={openYoruba}
              className="send-btn"
              style={{
                padding: "10px 14px",
                borderRadius: 14,
                border: "1px solid rgba(214,178,94,.55)",
                background: "rgba(0,0,0,.35)",
                color: "#f5e6b3",
                cursor: "pointer",
              }}
            >
              🌍 Yoruba Lessons
            </button>
          </div>
        </div>

        {/* Chat Window */}
        <div className="chat-window" id="chat-output">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              <div>
                {msg.text}
                {msg.audio_url && (
                  <audio controls preload="auto" className="voice-reply">
                    <source src={msg.audio_url} type="audio/mpeg" />
                    Your browser does not support audio playback.
                  </audio>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-bubble assistant thinking">
              🦁 Mufasa is thinking...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your question to Mufasa..."
          />
          <button
            type="button"
            className={`send-btn ${loading ? "disabled" : ""}`}
            onClick={handleSend}
            disabled={loading}
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>

        {/* Voice Controls */}
        <VoiceControls latestMessage={latestReply} onVoiceSend={handleVoiceInput} />
      </main>
    </div>
  );
}
