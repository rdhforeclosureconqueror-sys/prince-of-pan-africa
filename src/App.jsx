import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import AdminDashboardAI from "./pages/AdminDashboardAI";
import FitnessPage from "./pages/FitnessPage";
import Home from "./pages/Home";
import LanguagePage from "./pages/LanguagePage";
import TimelinePage from "./pages/TimelinePage";
import UniverseOverlay from "./components/UniverseOverlay";

export default function App() {
  // Simple example auth logic (replace with your real one)
  const isAuthenticated = localStorage.getItem("auth_token");

  return (
    <Router>
      <UniverseOverlay />
      <Routes>
        {/* Public route for login */}
        <Route path="/" element={<Home />} />

        {/* Protected layout with all inner routes */}
        {isAuthenticated ? (
          <Route element={<AppLayout />}>
            {/* Default redirect to AdminDashboardAI after login */}
            <Route path="/dashboard" element={<AdminDashboardAI />} />
            <Route path="/fitness" element={<FitnessPage />} />
            <Route path="/history" element={<TimelinePage />} />
            <Route path="/languages" element={<LanguagePage />} />
            {/* Redirect root to dashboard */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        ) : (
          // If not logged in, redirect to login
          <Route path="*" element={<Navigate to="/" replace />} />
        )}
      </Routes>
    </Router>
  );
}
