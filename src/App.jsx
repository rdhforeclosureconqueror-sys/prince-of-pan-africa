import React, { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import GlobalNav from "./components/GlobalNav";
import UniverseOverlay from "./components/UniverseOverlay";
import AdminOperationsDashboard from "./pages/AdminOperationsDashboard";
import Home from "./pages/Home";
import LanguagesHub from "./pages/LanguagesHub";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import PortalDecolonize from "./pages/PortalDecolonize";
import TimelinePage from "./pages/TimelinePage";
import MemberDashboard from "./pages/MemberDashboard";
import LeadershipAssessmentPage from "./pages/LeadershipAssessmentPage";
import LeadershipResultsPage from "./pages/LeadershipResultsPage";
import SystemVerificationPage from "./pages/SystemVerificationPage";
import PilotDeferredPage from "./pages/PilotDeferredPage";
import StudyPage from "./pages/StudyPage";
import { getBackgroundForPath } from "./utils/backgroundSystem";
import { API_BASE_URL } from "./config";
import "./styles/backgroundSystem.css";

const API = API_BASE_URL;

function AppRoutes({ user, isAdmin, refreshAuth, dashboardElement }) {
  return (
    <>
      <GlobalNav isAdmin={isAdmin} isAuthed={!!user} />
      <Routes>
        <Route path="/" element={<Home user={user} isAdmin={isAdmin} onAuthChange={refreshAuth} />} />
        <Route path="/dashboard" element={dashboardElement} />
        <Route path="/admin-legacy" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/fitness"
          element={
            <PilotDeferredPage
              title="Fitness is deferred for pilot"
              detail="Coach launch and session telemetry remain out of the Phase 4 pilot lock."
            />
          }
        />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/history" element={<TimelinePage />} />
        <Route path="/languages" element={<LanguagesHub />} />
        <Route
          path="/language-practice"
          element={
            <PilotDeferredPage title="Language Practice is deferred for pilot" />
          }
        />
        <Route path="/calendar" element={<PilotDeferredPage title="Calendar is deferred for pilot" />} />
        <Route path="/journal" element={<PilotDeferredPage title="Journal is deferred for pilot" />} />
        <Route path="/ledger" element={<PilotDeferredPage title="Ledger is deferred for pilot" />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/pagt" element={<PilotDeferredPage title="Pan-Africa’s Got Talent is deferred for pilot" />} />
        <Route path="/membership" element={<PilotDeferredPage title="Membership plan is deferred for pilot" />} />
        <Route path="/leadership" element={<LeadershipAssessmentPage />} />
        <Route path="/results" element={<LeadershipResultsPage />} />
        <Route path="/ops/verification" element={<SystemVerificationPage />} />
        <Route path="/decolonize" element={<LibraryDecolonize />} />
        <Route path="/portal/decolonize" element={<PortalDecolonize />} />
        <Route path="/holistic" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

function CosmicBackgroundLayer() {
  const location = useLocation();

  useEffect(() => {
    const { image } = getBackgroundForPath(location.pathname);
    document.documentElement.style.setProperty("--cosmic-bg-image", `url('${image}')`);
  }, [location.pathname]);

  return <UniverseOverlay />;
}

export default function App() {
  const [user, setUser] = useState(null);

  const adminEmails = useMemo(() => {
    const raw = import.meta.env.VITE_ADMIN_EMAILS || "";
    return raw
      .split(",")
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean);
  }, []);

  const refreshAuth = useCallback(async () => {
    try {
      const res = await fetch(`${API}/auth/me`, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      const data = res.ok ? await res.json() : null;
      setUser(data?.user || null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const isAdmin = useMemo(() => {
    if (!user) return false;
    if (user?.role === "admin" || user?.is_admin) return true;
    if (user?.email && adminEmails.includes(user.email.toLowerCase())) return true;
    return false;
  }, [user, adminEmails]);

  const dashboardElement = isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;

  return (
    <Router>
      <CosmicBackgroundLayer />
      <AppRoutes
        user={user}
        isAdmin={isAdmin}
        refreshAuth={refreshAuth}
        dashboardElement={dashboardElement}
      />
    </Router>
  );
}
