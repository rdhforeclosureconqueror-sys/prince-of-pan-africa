import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import VoiceControls from "../components/VoiceControls";
import { sendChatMessage, sendVoiceMessage } from "../api/mufasaClient";
import { API_BASE_URL, API_DEBUG, ENABLE_TEXT_BOOK_ORGANIZER } from "../config";
import { api } from "../api/api";
import "../styles/home.css";

const API_BASE = API_BASE_URL;

const capabilityCards = [
  {
    eyebrow: "Library",
    title: "Books & Audiobooks Library",
    description:
      "Explore a growing library of books, audiobooks, and educational materials organized for cultural learning, leadership development, and self-directed study.",
    cta: "Open Library",
    to: "/library",
  },
  {
    eyebrow: "Language",
    title: "Language Learning",
    description:
      "Begin building language connection through Swahili and other learning resources designed to reconnect culture, communication, and identity.",
    cta: "Explore Language Lessons",
    to: "/languages",
  },
  {
    eyebrow: "History",
    title: "Historical Learning Paths",
    description:
      "Study history through curated timelines and learning paths that connect past struggles, present conditions, and future institution-building.",
    cta: "Explore History",
    to: "/timeline",
  },
  {
    eyebrow: "Assessment",
    title: "Leadership Assessment",
    description:
      "Take assessments that help members reflect on leadership, readiness, discipline, and personal development.",
    cta: "Start Assessment",
    to: "/assessments",
  },
  {
    eyebrow: "Preparedness",
    title: "Preparedness Center",
    description:
      "Build practical readiness for your household and community through preparedness education, planning, and action-based learning.",
    cta: "Open Preparedness Center",
    to: "/community/preparedness",
  },
];

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
    return authMode === "join" ? "Join the Community" : "Sign in";
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
  const dashboardLabel = isAdmin ? "Open Operations Deck" : "Open Member Dashboard";

  return (
    <div className="home-shell">
      <section className="hero-panel cosmic-readable-shell">
        <p className="hero-kicker">SIMBA WA UJAMAA</p>
        <h1>Mufasa The Decolonizer</h1>
        <p className="hero-subtitle">
          A Pan-African learning and preparedness platform for language, history, leadership, cooperative economics,
          books, audiobooks, assessments, and community-building.
        </p>
        <div className="hero-cta-row">
          {authChecked && user ? (
            <Link to="/dashboard" className="hero-btn">{dashboardLabel}</Link>
          ) : (
            <a href="#join" className="hero-btn" onClick={() => setAuthMode("join")}>Join the Community</a>
          )}
          <Link to="/library" className="hero-btn hero-btn--secondary">Explore the Library</Link>
          <Link to="/assessments" className="hero-btn hero-btn--ghost">Assessment Center</Link>
          {!user ? <a href="#join" className="hero-btn hero-btn--ghost" onClick={() => setAuthMode("login")}>Sign In</a> : null}
        </div>
      </section>

      <section className="panel intro-panel cosmic-readable-shell" aria-labelledby="what-is-mufasa">
        <p className="section-kicker">What is Mufasa Universe?</p>
        <h2 id="what-is-mufasa">A digital learning home for culture, discipline, and community capacity.</h2>
        <p>
          Mufasa Universe is a digital learning home for people building knowledge, discipline, culture, and
          community capacity. Members can study Pan-African history, explore books and audiobooks, practice
          language, take leadership assessments, prepare for emergencies, and follow guided learning paths from
          one dashboard.
        </p>
      </section>

      <section className="capability-section" aria-labelledby="capabilities-title">
        <div className="section-heading cosmic-readable-shell">
          <p className="section-kicker">Explore the Universe</p>
          <h2 id="capabilities-title">Learning, readiness, and institution-building in one platform.</h2>
        </div>

        <div className="capability-grid">
          {capabilityCards.map((card) => (
            <article className="panel capability-card cosmic-readable-shell" key={card.title}>
              <p className="card-eyebrow">{card.eyebrow}</p>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
              <Link to={card.to} className="hero-btn hero-btn--small">{card.cta}</Link>
            </article>
          ))}

          <article className="panel capability-card cosmic-readable-shell">
            <p className="card-eyebrow">Member Hub</p>
            <h3>Member Dashboard</h3>
            <p>
              Your dashboard brings your learning, assessments, library activity, and community tools into one
              daily hub.
            </p>
            {authChecked && user ? (
              <Link to="/dashboard" className="hero-btn hero-btn--small">{dashboardLabel}</Link>
            ) : (
              <a href="#join" className="hero-btn hero-btn--small" onClick={() => setAuthMode("join")}>Join to Access Dashboard</a>
            )}
          </article>

          <article className="panel capability-card cosmic-readable-shell">
            <p className="card-eyebrow">Builder Access</p>
            <h3>Builder Access</h3>
            <p>
              Eligible Builder Members and administrators can access advanced tools for organizing content,
              creating learning resources, and supporting the growth of the platform.
            </p>
            {ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer ? (
              <Link to="/library/organizer" className="hero-btn hero-btn--small">Open Builder Tools</Link>
            ) : (
              <Link to="/membership" className="hero-btn hero-btn--small">View Membership Options</Link>
            )}
          </article>
        </div>
      </section>

      <section className="membership-panel panel cosmic-readable-shell">
        <p className="section-kicker">Membership</p>
        <h2>Choose Your Level of Access</h2>
        <p>
          Membership supports the continued development of the Mufasa Universe and unlocks access to the learning
          dashboard, assessments, preparedness tools, library experiences, and eligible member features.
        </p>
        <div className="hero-cta-row">
          <Link to="/membership" className="hero-btn">View Membership Options</Link>
          {authChecked && user ? (
            <Link to="/dashboard" className="hero-btn hero-btn--secondary">{dashboardLabel}</Link>
          ) : (
            <a href="#join" className="hero-btn hero-btn--secondary" onClick={() => setAuthMode("join")}>Join Now</a>
          )}
        </div>
      </section>

      <section className="home-grid" id="join">
        <article className="panel account-panel cosmic-readable-shell">
          <h2>{authTitle}</h2>
          {user ? (
            <>
              <p className="panel-text">
                Signed in as <strong>{user.email}</strong> ({isAdmin ? "admin" : "member"}).
              </p>
              <div className="hero-cta-row">
                <Link to="/dashboard" className="hero-btn hero-btn--secondary">{dashboardLabel}</Link>
                <Link to="/membership" className="hero-btn hero-btn--ghost">Membership Options</Link>
                <button type="button" onClick={logout} className="hero-btn hero-btn--ghost">Sign out</button>
              </div>
            </>
          ) : (
            <form className="auth-form" onSubmit={submitAuth}>
              <p className="panel-text">
                Create your member account or sign in to continue into your learning dashboard, assessments, and
                member tools.
              </p>
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
          <p className="section-kicker">Start Here</p>
          <h2>Explore before you join.</h2>
          <ul className="focus-list">
            <li>Open the library and begin exploring books, audiobooks, and study materials.</li>
            <li>Visit language lessons and historical learning paths to see the learning focus.</li>
            <li>Join when you are ready to continue through the member dashboard and gated tools.</li>
          </ul>
          <div className="hero-cta-row">
            <Link to="/library" className="hero-btn hero-btn--secondary">Open Library</Link>
            <Link to="/languages" className="hero-btn hero-btn--ghost">Language Lessons</Link>
          </div>
        </article>
      </section>

      <section className="panel chat-panel cosmic-readable-shell">
        <p className="section-kicker">Ask Mufasa</p>
        <h2>Ask Mufasa</h2>
        <p className="panel-text">
          Ask questions about the platform, learning paths, books, language, history, and member tools.
        </p>
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
