import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import AdminDashboardAI from "./pages/AdminDashboardAI";
import FitnessPage from "./pages/FitnessPage";
import HistoryPage from "./pages/HistoryPage";
import LanguagePage from "./pages/LanguagePage";
import LoginPage from "./pages/LoginPage";
import "./styles/global.css";

export default function App() {
  // Simple example auth logic (replace with your real one)
  const isAuthenticated = localStorage.getItem("auth_token");

  return (
    <Router>
      <Routes>
        {/* Public route for login */}
        <Route path="/" element={<LoginPage />} />

        {/* Protected layout with all inner routes */}
        {isAuthenticated ? (
          <Route element={<AppLayout />}>
            {/* Default redirect to AdminDashboardAI after login */}
            <Route path="/dashboard" element={<AdminDashboardAI />} />
            <Route path="/fitness" element={<FitnessPage />} />
            <Route path="/history" element={<HistoryPage />} />
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
