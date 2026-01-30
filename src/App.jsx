import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import GlobalNav from "./components/GlobalNav";
import UniverseOverlay from "./components/UniverseOverlay";
import AdminOperationsDashboard from "./pages/AdminOperationsDashboard";
import CalendarPage from "./pages/CalendarPage";
import FitnessPage from "./pages/FitnessPage";
import Home from "./pages/Home";
import JournalPage from "./pages/JournalPage";
import LanguagePage from "./pages/LanguagePage";
import LanguagesHub from "./pages/LanguagesHub";
import LedgerPage from "./pages/LedgerPage";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import MembershipPlan from "./pages/MembershipPlan";
import PagtPage from "./pages/PagtPage";
import PortalDecolonize from "./pages/PortalDecolonize";
import StudyPage from "./pages/StudyPage";
import TimelinePage from "./pages/TimelinePage";

export default function App() {
  return (
    <Router>
      <UniverseOverlay />
      <GlobalNav />
      <Routes>
        {/* Landing */}
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<AdminOperationsDashboard />} />
        <Route path="/admin-legacy" element={<Navigate to="/dashboard" replace />} />
        <Route path="/fitness" element={<FitnessPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/history" element={<TimelinePage />} />
        <Route path="/languages" element={<LanguagesHub />} />
        <Route path="/language-practice" element={<LanguagePage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/ledger" element={<LedgerPage />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/pagt" element={<PagtPage />} />
        <Route path="/membership" element={<MembershipPlan />} />
        <Route path="/decolonize" element={<LibraryDecolonize />} />
        <Route path="/portal/decolonize" element={<PortalDecolonize />} />
        <Route path="/holistic" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
