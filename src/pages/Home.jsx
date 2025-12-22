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
        audio_url: reply.audio_url || null,
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

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
// 🎤 Handle Voice Input (Fixed)
const handleVoiceInput = async (audioBlob) => {
  if (loading) return;

  setLoading(true);

  // Optional placeholder while we wait
  setMessages((prev) => [
    ...prev,
    { role: "user", text: "🎙️ You spoke to Mufasa..." },
  ]);

  try {
    const data = await sendVoiceMessage(audioBlob);

    // data might be { transcript, reply, audio_url } or similar
    const transcript =
      data?.transcript || data?.text || data?.user_text || null;

    const replyText =
      data?.reply ||
      data?.response ||
      data?.answer ||
      data?.message ||
      (typeof data === "string" ? data : "") ||
      "🦁 Mufasa is silent...";

    // If transcript exists, replace the placeholder user message with transcript
    if (transcript) {
      setMessages((prev) => {
        const next = [...prev];
        // Replace the last user placeholder we just added
        for (let i = next.length - 1; i >= 0; i--) {
          if (next[i].role === "user" && next[i].text.includes("You spoke")) {
            next[i] = { role: "user", text: `🎙️ ${transcript}` };
            break;
          }
        }
        return next;
      });
    }

    // Normalize audio_url (sometimes backend returns full URL, sometimes "/static/...")
    const baseURL = "https://mufasa-knowledge-bank.onrender.com";
    const rawAudio = data?.audio_url || data?.audioUrl || null;

    const fullAudioUrl =
      rawAudio && rawAudio.startsWith("http") ? rawAudio : rawAudio ? `${baseURL}${rawAudio}` : null;

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

  // Get latest AI message for VoiceControls
  const latestReply = messages
    .filter((msg) => msg.role === "assistant")
    .slice(-1)[0]?.text || "";

  return (
    <div className="app-container">
      <JournalSidebar />

      <main className="chat-area">
        {/* Header */}
        <div className="chat-header">
          <h1 className="title">Prince of Pan-Africa</h1>
          <p className="subtitle">
            Every month is Black History. Powered by{" "}
            <span className="mufasa">Mufasa</span>.
          </p>
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
