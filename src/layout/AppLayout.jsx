import React from "react";
import { Outlet, Link } from "react-router-dom";
import "../styles/layout.css";

export default function AppLayout() {
  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="logo">🧠 Ma’at 2.0</div>
        <div className="nav-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/fitness">Fitness</Link>
          <Link to="/history">History</Link>
          <Link to="/languages">Languages</Link>
          <Link to="/">Home</Link>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
