import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
import AdminDashboard from "./pages/AdminDashboard";
import AdminDashboardAI from "./pages/AdminDashboardAI";
import TimelinePage from "./pages/TimelinePage";
import MembershipPlan from "./pages/MembershipPlan";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />

        {/* Dashboards */}
        <Route path="/dashboard" element={<HolisticDashboard />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/ai" element={<AdminDashboardAI />} />

        {/* Core Pages */}
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
      </Routes>
    </BrowserRouter>
  );
}

export default App;
