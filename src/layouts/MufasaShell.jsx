import { Outlet, NavLink } from "react-router-dom";
import "../styles/MufasaShell.css";

export default function MufasaShell() {
  return (
    <div className="mufasa-shell">
      {/* Header */}
      <header className="mufasa-header">
        <div className="brand">
          <img src="/assets/lion-logo.png" alt="Mufasa Logo" className="lion-logo" />
          <div>
            <h1 className="brand-title">Prince of Pan-Africa</h1>
            <p className="brand-subtitle">Black History • Year-Round • Powered by MufasaBrain</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="nav-bar">
          <NavLink to="/" className="nav-item">Ask</NavLink>
          <NavLink to="/timeline" className="nav-item">Timeline</NavLink>
         <NavLink to="/library" className="nav-item">Decolonization</NavLink>
          <NavLink to="/calendar" className="nav-item">Calendar</NavLink>
          <NavLink to="/journal" className="nav-item">Journal</NavLink>
          <NavLink to="/membership" className="nav-item">30-Day Plan</NavLink>
        </nav>
      </header>

      {/* Main Content */}
      <main className="mufasa-content">
        <Outlet /> {/* All subpages (chat, calendar, journal, etc.) render here */}
      </main>

      {/* Footer */}
      <footer className="mufasa-footer">
        <p>Every Month Is Black History · <strong>Powered by MufasaBrain</strong></p>
      </footer>
    </div>
  );
}
