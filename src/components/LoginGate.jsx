// src/components/LoginGate.jsx
import { useEffect, useState } from "react";
import { API_BASE } from "../config";

export default function LoginGate({ children }) {
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);

  async function fetchMe() {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
      if (!res.ok) throw new Error("not authed");
      const data = await res.json();
      setMe(data.user);
    } catch {
      setMe(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMe();
  }, []);

  function login() {
    // sends user to API -> Google -> back to site
    window.location.href = `${API_BASE}/auth/google`;
  }

  if (loading) {
    return (
      <div style={styles.center}>
        <div>Loading…</div>
      </div>
    );
  }

  // If NOT logged in -> show video + modal gate
  if (!me) {
    return (
      <div style={styles.page}>
        <video
          style={styles.video}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        >
          <source src="/video/lion-run.mp4" type="video/mp4" />
        </video>

        <div style={styles.overlay} />

        <div style={styles.modal}>
          <div style={styles.title}>Are you human?</div>

          <div style={styles.text}>
            Sign in with Google to enter.
            <br />
            <span style={styles.subtext}>
              Signing in does <b>not</b> create a membership or require payment.
              It’s only used to verify you and protect the site.
            </span>
          </div>

          <button style={styles.button} onClick={login}>
            Sign in with Google
          </button>

          <div style={styles.footerText}>
            Protected access • SIMBA Wa Ujamaa
          </div>
        </div>
      </div>
    );
  }

  // Logged in -> allow site to render
  return (
    <>
      {children}
      {/* You can remove this later; it’s helpful while testing */}
      <div style={styles.cornerTag}>
        ✅ Signed in as: {me.email || me.displayName || "User"}
      </div>
    </>
  );
}

const styles = {
  page: {
    position: "relative",
    width: "100%",
    minHeight: "100vh",
    overflow: "hidden",
    background: "#000",
  },
  video: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    filter: "contrast(1.1) saturate(1.1)",
  },
  overlay: {
    position: "absolute",
    inset: 0,
    background:
      "linear-gradient(180deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.75) 50%, rgba(0,0,0,0.85) 100%)",
  },
  modal: {
    position: "relative",
    zIndex: 2,
    maxWidth: 520,
    margin: "0 auto",
    top: "14vh",
    padding: 24,
    borderRadius: 16,
    background: "rgba(0,0,0,0.55)",
    border: "1px solid rgba(255,255,255,0.18)",
    backdropFilter: "blur(10px)",
    textAlign: "center",
    color: "#fff",
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  text: {
    fontSize: 16,
    lineHeight: 1.4,
    opacity: 0.95,
    marginBottom: 18,
  },
  subtext: {
    display: "inline-block",
    marginTop: 10,
    fontSize: 13,
    opacity: 0.85,
  },
  button: {
    width: "100%",
    padding: "12px 16px",
    borderRadius: 12,
    border: "none",
    fontWeight: 800,
    cursor: "pointer",
  },
  footerText: {
    marginTop: 14,
    fontSize: 12,
    opacity: 0.75,
  },
  center: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    background: "#000",
    color: "#fff",
  },
  cornerTag: {
    position: "fixed",
    right: 10,
    bottom: 10,
    background: "rgba(0,0,0,0.6)",
    color: "#fff",
    padding: "8px 10px",
    borderRadius: 10,
    fontSize: 12,
    zIndex: 9999,
    border: "1px solid rgba(255,255,255,0.15)",
  },
};
