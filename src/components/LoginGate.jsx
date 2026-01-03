// ✅ src/components/LionGate.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LionGate({ children }) {
  const navigate = useNavigate();

  // Base API URL (from your config or .env)
  const API = import.meta.env.VITE_API_BASE_URL || "https://api.simbawaujamaa.com";

  const [status, setStatus] = useState("checking"); // checking | authed | guest | error
  const [user, setUser] = useState(null);
  const [err, setErr] = useState("");

  const videoSrc = useMemo(() => "/asset/video/lion-run.mp4", []);

  // 🧠 Check session
  async function checkMe() {
    setErr("");
    setStatus("checking");

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

      if (data?.ok && data?.auth) {
        setStatus("authed");
        setUser(data.user);

        // ✅ If admin → go straight to admin page
        if (data.user.role === "admin") {
          navigate("/admin", { replace: true });
        }
      } else {
        setStatus("guest");
        setUser(null);
      }
    } catch (e) {
      console.error("❌ LionGate check failed:", e);
      setStatus("error");
      setErr(e?.message || "Network error");
    }
  }

  useEffect(() => {
    checkMe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 🦁 Trigger Google OAuth login
  function startLogin() {
    window.location.href = `${API}/auth/google`;
  }

  // 🦁 If authenticated, show the app
  if (status === "authed") {
    return children;
  }

  // 🦁 Otherwise show gate screen
  return (
    <div style={styles.wrap}>
      {/* Background Video */}
      <video
        src={videoSrc}
        autoPlay
        muted
        loop
        playsInline
        style={styles.video}
      />

      {/* Overlay */}
      <div style={styles.overlay} />

      {/* Gate Modal */}
      <div style={styles.modal}>
        <div style={styles.title}>🦁 LionGate</div>
        <div style={styles.sub}>Verify your humanity to enter MufasaBrain.</div>

        <button onClick={startLogin} style={styles.button}>
          Sign in with Google
        </button>

        <div style={styles.note}>
          This is a secure Google verification — no payment or membership yet.
        </div>

        <div style={styles.small}>
          {status === "checking" && "Checking your session..."}
          {status === "guest" && "Not signed in yet."}
          {status === "error" && `Error: ${err}`}
        </div>

        {status !== "checking" && (
          <button onClick={checkMe} style={styles.linkBtn}>
            🔄 Refresh login status
          </button>
        )}
      </div>
    </div>
  );
}

// 🎨 Styles (cinematic look)
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
    filter: "contrast(1.1) saturate(1.05) brightness(0.95)",
  },
  overlay: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(180deg, rgba(0,0,0,0.6), rgba(0,0,0,0.75))",
  },
  modal: {
    position: "relative",
    width: "min(520px, 92vw)",
    borderRadius: 16,
    padding: 24,
    background: "rgba(10,10,10,0.8)",
    border: "1px solid rgba(255,255,255,0.12)",
    boxShadow: "0 0 25px rgba(255, 255, 255, 0.1)",
    backdropFilter: "blur(14px)",
    color: "#fff",
    textAlign: "center",
    fontFamily: "Poppins, system-ui, sans-serif",
  },
  title: {
    fontSize: 30,
    fontWeight: 800,
    marginBottom: 6,
    color: "#FFD700",
    textShadow: "0 0 8px rgba(255,215,0,0.4)",
  },
  sub: { fontSize: 15, opacity: 0.9, marginBottom: 16 },
  button: {
    width: "100%",
    padding: "12px 14px",
    borderRadius: 12,
    border: "none",
    cursor: "pointer",
    fontWeight: 700,
    fontSize: 16,
    background: "linear-gradient(90deg, #ffb300, #ffcc00)",
    color: "#000",
    transition: "0.3s",
  },
  note: { marginTop: 12, fontSize: 12, opacity: 0.85, lineHeight: 1.4 },
  small: { marginTop: 12, fontSize: 12, opacity: 0.75 },
  linkBtn: {
    marginTop: 10,
    background: "transparent",
    border: "none",
    color: "#FFD700",
    opacity: 0.85,
    textDecoration: "underline",
    cursor: "pointer",
    fontSize: 12,
  },
};
