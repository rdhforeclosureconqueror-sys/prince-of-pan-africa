import React, { useMemo, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import GlobalNav from "./components/GlobalNav";
import UniverseOverlay from "./components/UniverseOverlay";
import LionGate from "./components/LionGate";
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
import MemberDashboard from "./pages/MemberDashboard";

export default function App() {
  const [user, setUser] = useState(null);

  const adminEmails = useMemo(() => {
    const raw = import.meta.env.VITE_ADMIN_EMAILS || "";
    return raw
      .split(",")
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean);
  }, []);

  const isAdmin = useMemo(() => {
    if (!user) return false;
    if (user?.role === "admin" || user?.is_admin) return true;
    if (user?.email && adminEmails.includes(user.email.toLowerCase())) return true;
    return false;
  }, [user, adminEmails]);

  const dashboardElement = isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;

  return (
    <Router>
      <UniverseOverlay />
      <LionGate onAuth={setUser}>
        <GlobalNav isAdmin={isAdmin} />
        <Routes>
          {/* Landing */}
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={dashboardElement} />
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
      </LionGate>
    </Router>
  );
}
