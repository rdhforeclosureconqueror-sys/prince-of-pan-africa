import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import VoiceControls from "../components/VoiceControls";
import { sendChatMessage, sendVoiceMessage } from "../api/mufasaClient";
import { API_BASE_URL, API_DEBUG, ENABLE_TEXT_BOOK_ORGANIZER } from "../config";
import { api } from "../api/api";
import "../styles/home.css";

const API_BASE = API_BASE_URL;

export default function Home({ user, isAdmin, canAccessOrganizer = false, authChecked = false, onAuthChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const [authMode, setAuthMode] = useState("join");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authStatus, setAuthStatus] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);


  useEffect(() => {
    const requestedAuthMode = (searchParams.get("auth") || "").toLowerCase();
    if (requestedAuthMode === "login" || requestedAuthMode === "join") {
      setAuthMode(requestedAuthMode);
    }
  }, [searchParams]);

  const authTitle = useMemo(() => {
    if (isAdmin) return "Admin access active";
    if (user) return "Member access active";
    return authMode === "join" ? "Join as a member" : "Sign in";
  }, [authMode, isAdmin, user]);

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
      if (API_DEBUG) {
        console.info("[runtime] auth request URL", `${API_BASE}${endpoint}`);
      }
      await api(endpoint, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setAuthStatus(authMode === "join" ? "Member account created." : "Signed in.");
      setPassword("");
      await onAuthChange();
    } catch (err) {
      setAuthStatus(err.message || "Authentication failed");
    }
  }

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    setAuthStatus("Signed out.");
    await onAuthChange();
  }

  const latestReply = messages.filter((msg) => msg.role === "assistant").slice(-1)[0]?.text || "";

  return (
    <div className="home-shell">
      <section className="hero-panel cosmic-readable-shell">
        <p className="hero-kicker">Simba wa Ujamaa</p>
        <h1>Mufasa The Decolonizer</h1>
        <p className="hero-subtitle">
          Join a Pan-African learning community rooted in language, history, leadership, and cooperative institution building.
        </p>
        <div className="hero-cta-row">
          <Link to="/library" className="hero-btn">Books & Audiobooks Library</Link>
          {user && ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer ? (
            <>
              <Link to="/library/organizer" className="hero-btn hero-btn--secondary">Format a Book</Link>
              <Link to="/library/organizer" className="hero-btn hero-btn--secondary">Upload Book Text</Link>
            </>
          ) : null}
          {authChecked && user ? (
            <Link to="/dashboard" className="hero-btn hero-btn--ghost">{isAdmin ? "Operations Deck" : "Member Dashboard"}</Link>
          ) : null}
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
                {ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer ? (
                  <Link to="/library/organizer" className="hero-btn">Upload Book Text</Link>
                ) : null}
                <Link to="/dashboard" className="hero-btn hero-btn--secondary">{isAdmin ? "Open Operations Deck" : "Open Member Dashboard"}</Link>
                {authChecked && ENABLE_TEXT_BOOK_ORGANIZER && user && !canAccessOrganizer ? (
                  <span className="access-note">Text Book Organizer is available to Builder Member, admin, and superadmin accounts.</span>
                ) : null}
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
          <h2>Public Homepage</h2>
          <ul className="focus-list">
            <li>Explore the library, language lessons, leadership assessment, and historical learning paths.</li>
            <li>Members continue from a dedicated dashboard built as a daily community hub.</li>
            <li>Builder tools remain permission-gated for eligible members and administrators.</li>
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
