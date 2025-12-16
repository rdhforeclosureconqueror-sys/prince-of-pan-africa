import { useState, useEffect, useRef } from "react";
import VoiceControls from "../components/VoiceControls";
import JournalSidebar from "../components/JournalSidebar";
import "../styles/theme.css";
import { sendChatMessage } from "../api/mufasaClient";

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
            <div
              key={i}
              className={`chat-bubble ${
                msg.role === "user" ? "user" : "assistant"
              }`}
            >
              {msg.text}
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
        <VoiceControls latestMessage={latestReply} />
      </main>
    </div>
  );
}
