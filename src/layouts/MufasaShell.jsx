// ✅ src/layouts/MufasaShell.jsx
import React, { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import LogoutButton from "../components/LogoutButton";
import "../styles/MufasaShell.css";

export default function MufasaShell({ children }) {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 🌌 Dynamic Background (Galaxy / Fitness / Language)
  useEffect(() => {
    const path = location.pathname;

    if (path.includes("fitness")) {
      document.body.style.background =
        "linear-gradient(135deg, #ff8c00, #b21f1f)";
    } else if (path.includes("language")) {
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

  useEffect(() => {
    setUser({
      id: "prototype-user",
      displayName: "Prototype Admin",
      role: "admin",
    });
  }, []);

  const linkClass = ({ isActive }) => `nav-item${isActive ? " active" : ""}`;

  return (
    <div className="mufasa-shell">
      {/* 🦁 Header */}
      <header className="mufasa-header">
        <div className="brand">
          <img src="/assets/lion-logo.png" alt="Mufasa Logo" className="lion-logo" />
          <div>
            <h1 className="brand-title">Prince of Pan-Africa</h1>
            <p className="brand-subtitle">
              Black History • Year-Round • Powered by MufasaBrain
            </p>
          </div>
        </div>

        {/* 🧭 Nav */}
        <nav className="nav-bar">
          <NavLink to="/" className={linkClass} end>Home</NavLink>
          <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/fitness" className={linkClass}>Fitness</NavLink>
          <NavLink to="/study" className={linkClass}>Study</NavLink>
          <NavLink to="/journal" className={linkClass}>Journal</NavLink>
          <NavLink to="/language" className={linkClass}>Language</NavLink>
          <NavLink to="/ledger" className={linkClass}>Ledger</NavLink>
          <NavLink to="/library" className={linkClass}>Library</NavLink>
          <NavLink to="/portal" className={linkClass}>Portal</NavLink>
          <NavLink to="/timeline" className={linkClass}>Timeline</NavLink>
          <NavLink to="/membership" className={linkClass}>Membership</NavLink>

          {user?.role === "admin" && (
            <>
              <NavLink to="/admin" className={linkClass}>Admin</NavLink>
              <NavLink to="/admin/ai" className={linkClass}>AI Dashboard</NavLink>
            </>
          )}
        </nav>

        {/* 🧍 User Info */}
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

      {/* 🧾 Main Content */}
      <main className="mufasa-content">{children}</main>

      {/* 🌍 Footer */}
      <footer className="mufasa-footer">
        <p>Every Month Is Black History • <strong>Powered by MufasaBrain</strong></p>
      </footer>
    </div>
  );
}
