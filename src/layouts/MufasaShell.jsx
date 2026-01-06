// ✅ src/layouts/MufasaShell.jsx
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import LogoutButton from "../components/LogoutButton";

// 🧩 Import all needed styles
import "../styles/MufasaShell.css";
import "../styles/universe.css";
import "../styles/dashboard.css";
import "../styles/achievementToast.css";
import "../styles/xpOverlay.css";
import "../styles/themes.css";
import "../styles/ledgerV2.css";
import "../styles/admin.css";

export default function MufasaShell() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 🌌 Dynamic background logic
  useEffect(() => {
    const path = location.pathname;

    if (path.startsWith("/fitness")) {
      document.body.style.background =
        "linear-gradient(135deg, #ff8c00, #b21f1f)";
    } else if (path.startsWith("/language")) {
      document.body.style.background =
        "linear-gradient(to bottom right, #004400, #001100)";
    } else {
      document.body.style.background =
        "radial-gradient(circle at 20% 20%, #090909 0%, #000010 100%)";
    }

    document.body.style.backgroundAttachment = "fixed";
    document.body.style.backgroundSize = "cover";
    document.body.style.color = "var(--gold)";
  }, [location]);

  // 👤 Load user data
  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await fetch("/auth/me", { credentials: "include" });
        const data = await res.json();
        if (data.ok && data.auth) {
          setUser(data.user);
        }
      } catch (err) {
        console.error("Error loading user:", err);
      }
    }
    fetchUser();
  }, []);

  const linkClass = ({ isActive }) => `nav-item${isActive ? " active" : ""}`;

  return (
    <div className="mufasa-shell">
      {/* 🦁 HEADER */}
      <header className="mufasa-header">
        <div className="brand">
          <img
            src="/assets/lion-logo.png"
            alt="Mufasa Logo"
            className="lion-logo"
          />
          <div>
            <h1 className="brand-title">Prince of Pan-Africa</h1>
            <p className="brand-subtitle">
              Black History • Year-Round • Powered by MufasaBrain
            </p>
          </div>
        </div>

        {/* 🧭 NAVIGATION */}
        <nav className="nav-bar">
          <NavLink to="/" className={linkClass} end>
            Ask
          </NavLink>
          <NavLink to="/timeline" className={linkClass}>
            Timeline
          </NavLink>
          <NavLink to="/library" className={linkClass}>
            Decolonization
          </NavLink>
          <NavLink to="/calendar" className={linkClass}>
            Calendar
          </NavLink>
          <NavLink to="/journal" className={linkClass}>
            Journal
          </NavLink>
          <NavLink to="/membership" className={linkClass}>
            30-Day Plan
          </NavLink>
          <NavLink to="/ledger" className={linkClass}>
            Ledger
          </NavLink>
          <NavLink to="/ledger-v2" className={linkClass}>
            Ledger V2
          </NavLink>
          <NavLink to="/pagt" className={linkClass}>
            Pan-Africa Got Talent
          </NavLink>
          <NavLink to="/fitness" className={linkClass}>
            Fitness
          </NavLink>
          <NavLink to="/language" className={linkClass}>
            Languages
          </NavLink>

          {/* 🦁 ADMIN ACCESS */}
          {user?.role === "admin" && (
            <div className="admin-nav-group">
              <NavLink to="/admin" className={linkClass}>
                🦁 Admin
              </NavLink>
              <button
                className="admin-subbutton"
                onClick={() => navigate("/admin/overview")}
              >
                ⚙ Dashboard
              </button>
            </div>
          )}
        </nav>

        {/* 🧍 USER INFO */}
        {user && (
          <div className="user-info">
            <div className="user-meta">
              <span className="user-name">{user.displayName || "User"}</span>
              <span className={`user-role ${user.role}`}>
                {user.role === "admin" ? "🦁 Admin" : "👤 Member"}
              </span>
            </div>
            <LogoutButton />
          </div>
        )}
      </header>

      {/* MAIN CONTENT */}
      <main className="mufasa-content">
        <Outlet />
      </main>

      {/* FOOTER */}
      <footer className="mufasa-footer">
        <p>
          Every Month Is Black History •{" "}
          <strong>Powered by MufasaBrain</strong>
        </p>
      </footer>
    </div>
  );
}
