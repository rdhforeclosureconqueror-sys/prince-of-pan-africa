import React from "react";
import { Outlet, Link } from "react-router-dom";
import "./AppLayout.css";

export default function AppLayout() {
  return (
    <div className="app-layout">
      <nav className="navbar">
        <h2 className="logo">Ma’at 2.0</h2>
        <div className="nav-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/history">History</Link>
          <Link to="/languages">Languages</Link>
          <Link to="/fitness">Fitness Hub</Link>
        </div>
      </nav>

      <main className="main-content">
        <Outlet /> {/* This renders the current page */}
      </main>
    </div>
  );
}
