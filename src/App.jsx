import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MufasaShell from "./layouts/MufasaShell";

// ===== Import All Pages =====
import Home from "./pages/Home";
import HolisticDashboard from "./pages/HolisticDashboard";
import FitnessPage from "./pages/FitnessPage";
import StudyPage from "./pages/StudyPage";
import JournalPage from "./pages/JournalPage";
import LanguagePage from "./pages/LanguagePage";
import LanguagesHub from "./pages/LanguagesHub";
import LedgerPage from "./pages/LedgerPage";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import PortalDecolonize from "./pages/PortalDecolonize";
import TimelinePage from "./pages/TimelinePage";
import MembershipPlan from "./pages/MembershipPlan";
import AdminDashboard from "./pages/AdminDashboard";
import AdminDashboardAI from "./pages/AdminDashboardAI";

// ✅ App Component — Uses MufasaShell for layout and background management
export default function App() {
  return (
    <BrowserRouter>
      {/* 🦁 Wrap everything in MufasaShell for universal layout and theme */}
      <MufasaShell>
        <Routes>
          {/* 🌍 Public & Main Routes */}
          <Route path="/" element={<Home />} />

          {/* 🧭 Dashboards */}
          <Route path="/dashboard" element={<HolisticDashboard />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/ai" element={<AdminDashboardAI />} />

          {/* 💪 Functional Pages */}
          <Route path="/fitness" element={<FitnessPage />} />
          <Route path="/study" element={<StudyPage />} />
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/language" element={<LanguagePage />} />
          <Route path="/languages" element={<LanguagesHub />} />
          <Route path="/ledger" element={<LedgerPage />} />
          <Route path="/library" element={<LibraryDecolonize />} />
          <Route path="/portal" element={<PortalDecolonize />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/membership" element={<MembershipPlan />} />

          {/* ❌ Fallback Route */}
          <Route
            path="*"
            element={
              <div className="p-8 text-center">
                <h1 className="text-3xl font-bold text-red-500 mb-4">404</h1>
                <p className="text-gray-400">
                  The page you’re looking for doesn’t exist.
                </p>
              </div>
            }
          />
        </Routes>
      </MufasaShell>
    </BrowserRouter>
  );
}
