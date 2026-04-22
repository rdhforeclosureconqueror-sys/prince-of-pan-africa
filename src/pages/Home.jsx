import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import VoiceControls from "../components/VoiceControls";
import { sendChatMessage, sendVoiceMessage } from "../api/mufasaClient";
import { API_BASE_URL } from "../config";
import "../styles/home.css";

const API_BASE = API_BASE_URL;

export default function Home({ user, isAdmin, onAuthChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [authMode, setAuthMode] = useState("join");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authStatus, setAuthStatus] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const authTitle = useMemo(() => {
    if (user?.role === "admin" || user?.role === "superadmin") return "Admin access active";
    if (user) return "Member access active";
    return authMode === "join" ? "Join as a member" : "Sign in";
  }, [authMode, user]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendChatMessage(input);
      const replyText = typeof reply === "string" ? reply : reply.reply || "🦁 Mufasa is silent...";
      setMessages((prev) => [...prev, { role: "assistant", text: replyText, audio_url: reply?.audio_url || null }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "⚠️ Mufasa could not be reached." }]);
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

  const handleVoiceInput = async (audioBlob) => {
    if (loading) return;
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: "🎙️ You spoke to Mufasa..." }]);

    try {
      const data = await sendVoiceMessage(audioBlob);
      const transcript = data?.transcript || data?.text || null;
      const replyText = data?.reply || data?.response || "🦁 Mufasa is silent...";

      if (transcript) {
        setMessages((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i -= 1) {
            if (next[i].role === "user" && next[i].text.includes("You spoke")) {
              next[i] = { role: "user", text: `🎙️ ${transcript}` };
              break;
            }
          }
          return next;
        });
      }

      const rawAudio = data?.audio_url || data?.audioUrl || null;
      const fullAudioUrl = rawAudio ? (rawAudio.startsWith("http") ? rawAudio : `${API_BASE}${rawAudio}`) : null;
      setMessages((prev) => [...prev, { role: "assistant", text: replyText, audio_url: fullAudioUrl }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "⚠️ Voice chat failed to connect." }]);
    } finally {
      setLoading(false);
    }
  };

  async function submitAuth(e) {
    e.preventDefault();
    setAuthStatus("");
    const endpoint = authMode === "join" ? "/auth/join" : "/auth/login";

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Authentication failed");

      setAuthStatus(authMode === "join" ? "Member account created." : "Signed in.");
      setPassword("");
      await onAuthChange();
    } catch (err) {
      setAuthStatus(err.message || "Authentication failed");
    }
  }

  async function logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    setAuthStatus("Signed out.");
    await onAuthChange();
  }

  const latestReply = messages.filter((msg) => msg.role === "assistant").slice(-1)[0]?.text || "";

  return (
    <div className="home-shell">
      <section className="hero-panel cosmic-readable-shell">
        <p className="hero-kicker">Pan-African Intelligence Platform</p>
        <h1>Mufasa The Decolonizer</h1>
        <p className="hero-subtitle">
          A focused home for member onboarding, admin operations, decolonized learning, and leadership training.
        </p>
        <div className="hero-cta-row">
          <Link to="/decolonize" className="hero-btn">Decolonized Library</Link>
          <Link to="/dashboard" className="hero-btn hero-btn--secondary">Operations Deck</Link>
          <Link to="/leadership" className="hero-btn hero-btn--ghost">Leadership Assessment</Link>
        </div>
      </section>

      <section className="home-grid">
        <article className="panel account-panel cosmic-readable-shell">
          <h2>{authTitle}</h2>
          {user ? (
            <>
              <p className="panel-text">
                Signed in as <strong>{user.email}</strong> ({isAdmin ? "admin" : "member"}).
              </p>
              <div className="hero-cta-row">
                <Link to="/dashboard" className="hero-btn">Open dashboard</Link>
                <button type="button" onClick={logout} className="hero-btn hero-btn--ghost">Sign out</button>
              </div>
            </>
          ) : (
            <form className="auth-form" onSubmit={submitAuth}>
              <div className="auth-switch">
                <button type="button" className={authMode === "join" ? "is-active" : ""} onClick={() => setAuthMode("join")}>Join</button>
                <button type="button" className={authMode === "login" ? "is-active" : ""} onClick={() => setAuthMode("login")}>Sign In</button>
              </div>
              <input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
              <input type="password" minLength={6} required placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button className="hero-btn" type="submit">{authMode === "join" ? "Create Member Account" : "Sign In"}</button>
            </form>
          )}
          {authStatus ? <p className="status-line">{authStatus}</p> : null}
        </article>

        <article className="panel cosmic-readable-shell">
          <h2>Platform focus</h2>
          <ul className="focus-list">
            <li>Admin oversight and member onboarding are active now.</li>
            <li>Fitness surfaces remain deferred during this phase.</li>
            <li>Portal workflows are accessible from inside the library.</li>
            <li>Operations Deck monitors member and AI operations status.</li>
          </ul>
        </article>
      </section>

      <section className="panel chat-panel cosmic-readable-shell">
        <h2>Talk to Mufasa</h2>
        <div className="chat-window" id="chat-output">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.text}
              {msg.audio_url ? (
                <audio controls preload="auto" className="voice-reply">
                  <source src={msg.audio_url} type="audio/mpeg" />
                </audio>
              ) : null}
            </div>
          ))}
          {loading ? <div className="chat-bubble assistant thinking">🦁 Mufasa is thinking...</div> : null}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your question to Mufasa..."
          />
          <button type="button" className={`send-btn ${loading ? "disabled" : ""}`} onClick={handleSend} disabled={loading}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
        <VoiceControls latestMessage={latestReply} onVoiceSend={handleVoiceInput} />
      </section>
    </div>
  );
}
