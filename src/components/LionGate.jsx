// ✅ src/components/LionGate.jsx
import React, { useEffect, useMemo, useState } from "react";

export default function LionGate({ children, onAuth }) {
  const API = import.meta.env.VITE_API_BASE_URL || "";

  const [status, setStatus] = useState("checking"); // checking | authed | guest | error
  const [user, setUser] = useState(null);
  const [err, setErr] = useState("");

  const videoSrc = useMemo(() => "/asset/video/lion-run.mp4", []);

  async function checkMe() {
    setErr("");
    try {
      const res = await fetch(`${API}/auth/me`, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
      });

      if (!res.ok) {
        setStatus("guest");
        setUser(null);
        return;
      }

      const data = await res.json();
      if (data?.auth) {
        setStatus("authed");
        setUser(data.user || null);
        if (onAuth) onAuth(data.user || null);
      } else {
        setStatus("guest");
        setUser(null);
      }
    } catch (e) {
      setStatus("error");
      setErr(e?.message || "Network error");
    }
  }

  useEffect(() => {
    checkMe();
  }, []);

  function startLogin() {
    window.location.href = `${API}/auth/google`;
  }

  if (status === "authed") return children;

  return (
    <div style={styles.wrap}>
      <video src={videoSrc} autoPlay muted loop playsInline style={styles.video} />
      <div style={styles.overlay} />

      <div style={styles.modal}>
        <div style={styles.title}>🦁 Verify you’re human</div>
        <div style={styles.sub}>Sign in with Google to continue</div>

        <button onClick={startLogin} style={styles.button}>
          Sign in with Google
        </button>

        <div style={styles.note}>
          This sign-in doesn’t start a membership. It’s only for secure access.
        </div>

        <div style={styles.small}>
          {status === "checking" && "Checking session..."}
          {status === "guest" && "Not signed in yet."}
          {status === "error" && `Error: ${err}`}
        </div>

        {status !== "checking" && (
          <button onClick={checkMe} style={styles.linkBtn}>
            Refresh login status
          </button>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrap: {
    position: "fixed",
    inset: 0,
    overflow: "hidden",
    background: "#000",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
  },
  video: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    filter: "contrast(1.1) saturate(1.05)",
  },
  overlay: {
    position: "absolute",
    inset: 0,
    background: "rgba(0,0,0,0.55)",
  },
  modal: {
    position: "relative",
    width: "min(520px, 92vw)",
    borderRadius: 16,
    padding: 22,
    background: "rgba(10,10,10,0.75)",
    border: "1px solid rgba(255,255,255,0.12)",
    backdropFilter: "blur(10px)",
    color: "#fff",
    textAlign: "center",
  },
  title: { fontSize: 28, fontWeight: 800, marginBottom: 6 },
  sub: { fontSize: 14, opacity: 0.9, marginBottom: 14 },
  button: {
    width: "100%",
    padding: "12px 14px",
    borderRadius: 12,
    border: "none",
    cursor: "pointer",
    fontWeight: 700,
    fontSize: 16,
  },
  note: { marginTop: 12, fontSize: 12, opacity: 0.85, lineHeight: 1.4 },
  small: { marginTop: 12, fontSize: 12, opacity: 0.75 },
  linkBtn: {
    marginTop: 10,
    background: "transparent",
    border: "none",
    color: "#fff",
    opacity: 0.85,
    textDecoration: "underline",
    cursor: "pointer",
    fontSize: 12,
  },
};
