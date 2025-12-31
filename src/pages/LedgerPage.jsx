import { Outlet, NavLink } from "react-router-dom";
import "../styles/MufasaShell.css";

export default function MufasaShell() {
  // ✅ Active-state styling without changing your CSS setup
  const linkClass = ({ isActive }) => `nav-item${isActive ? " active" : ""}`;

  return (
    <div className="mufasa-shell">
      {/* Header */}
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

        {/* Navigation */}
        <nav className="nav-bar">
          {/* ✅ These paths assume your App.jsx routes under MufasaShell are:
              timeline, library, calendar, journal, membership, ledger, pagt
              (no leading slash in App.jsx, BUT in NavLink we can safely use absolute) */}

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

          {/* ✅ NEW: Ledger + Pan-Africa Got Talent */}
          <NavLink to="/ledger" className={linkClass}>
            Ledger
          </NavLink>

          <NavLink to="/pagt" className={linkClass}>
            Pan-Africa Got Talent
          </NavLink>
        </nav>
      </header>

      {/* Main Content */}
      <main className="mufasa-content">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mufasa-footer">
        <p>
          Every Month Is Black History · <strong>Powered by MufasaBrain</strong>
        </p>
      </footer>
    </div>
  );
}
