import React, { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import GlobalNav from "./components/GlobalNav";
import UniverseOverlay from "./components/UniverseOverlay";
import AdminOperationsDashboard from "./pages/AdminOperationsDashboard";
import Home from "./pages/Home";
import LanguagesHub from "./pages/LanguagesHub";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import PortalDecolonize from "./pages/PortalDecolonize";
import LibraryOrganizer from "./pages/LibraryOrganizer";
import TimelinePage from "./pages/TimelinePage";
import MemberDashboard from "./pages/MemberDashboard";
import LeadershipAssessmentPage from "./pages/LeadershipAssessmentPage";
import LeadershipResultsPage from "./pages/LeadershipResultsPage";
import SystemVerificationPage from "./pages/SystemVerificationPage";
import AuthDebugPage from "./pages/AuthDebugPage";
import PilotDeferredPage from "./pages/PilotDeferredPage";
import StudyPage from "./pages/StudyPage";
import BrainTraining from "./pages/BrainTraining";
import { BuilderMembershipPage, CommunityMembershipPage, MembershipOverviewPage } from "./pages/MembershipPages";
import { BillingCancelPage, BillingSuccessPage } from "./pages/BillingStatusPages";
import { getBackgroundForPath } from "./utils/backgroundSystem";
import { API_DEBUG, AUTH_DEBUG, ENABLE_TEXT_BOOK_ORGANIZER } from "./config";
import { api } from "./api/api";
import { canAccessTextBookOrganizer, isAdminUser } from "./authz";
import "./styles/backgroundSystem.css";

function DashboardRoute({ authChecked, user, rbac, isAdmin }) {
  const location = useLocation();

  useEffect(() => {
    if (!AUTH_DEBUG) return;

    const roles = Array.isArray(rbac?.roles) ? rbac.roles : [];
    const permissions = Array.isArray(rbac?.permissions) ? rbac.permissions : [];
    console.info("[auth-debug] dashboard route decision", {
      route: location.pathname,
      authChecked,
      email: user?.email || null,
      role: user?.role || null,
      roles,
      permissionCount: permissions.length,
      isAdmin,
      decision: !authChecked ? "loading" : !user ? "redirect-login" : isAdmin ? "operations-deck" : "member-dashboard",
    });
  }, [authChecked, user, rbac, isAdmin, location.pathname]);

  if (!authChecked) return <div className="admin-loading">Loading your dashboard...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  return isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;
}

function OrganizerAccessNotice({ title, detail }) {
  return (
    <main className="library-shell">
      <div className="library-inner cosmic-readable-shell">
        <h1>{title}</h1>
        <p>{detail}</p>
        <div className="library-actions">
          <Link to="/library" className="library-pill library-pill--green">Back to Library</Link>
          <Link to="/?auth=login" className="library-pill">Sign in</Link>
        </div>
      </div>
    </main>
  );
}

function OrganizerRoute({ authChecked, user, rbac, canAccessOrganizer }) {
  const location = useLocation();

  useEffect(() => {
    if (!AUTH_DEBUG) return;

    const roles = Array.isArray(rbac?.roles) ? rbac.roles : [];
    const permissions = Array.isArray(rbac?.permissions) ? rbac.permissions : [];
    console.info("[auth-debug] organizer route decision", {
      route: location.pathname,
      authChecked,
      email: user?.email || null,
      role: user?.role || null,
      roles,
      permissionCount: permissions.length,
      isAdmin: isAdminUser(user, rbac),
      canAccessOrganizer,
      decision: !ENABLE_TEXT_BOOK_ORGANIZER
        ? "feature-disabled"
        : !authChecked
          ? "loading"
          : !user
            ? "redirect-login"
            : canAccessOrganizer
              ? "organizer"
              : "access-required",
    });
  }, [authChecked, user, rbac, canAccessOrganizer, location.pathname]);

  if (!ENABLE_TEXT_BOOK_ORGANIZER) {
    return (
      <OrganizerAccessNotice
        title="Text Book Organizer is not enabled"
        detail="The organizer route is registered, but VITE_ENABLE_TEXT_BOOK_ORGANIZER is not enabled for this deployment."
      />
    );
  }

  if (!authChecked) return <div className="admin-loading">Checking your Text Book Organizer access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (canAccessOrganizer) return <LibraryOrganizer />;

  return (
    <OrganizerAccessNotice
      title="Text Book Organizer access required"
      detail="Upgrade to Builder Membership or contact support if your account should include book_organizer:create_self."
    />
  );
}

function AppRoutes({ user, rbac, isAdmin, canAccessOrganizer, authChecked, refreshAuth }) {
  return (
    <>
      <GlobalNav user={user} rbac={rbac} canAccessOrganizer={canAccessOrganizer} authChecked={authChecked} />
      <Routes>
        <Route path="/" element={<Home user={user} isAdmin={isAdmin} canAccessOrganizer={canAccessOrganizer} authChecked={authChecked} onAuthChange={refreshAuth} />} />
        <Route path="/dashboard" element={<DashboardRoute authChecked={authChecked} user={user} rbac={rbac} isAdmin={isAdmin} />} />
        <Route path="/admin" element={<Navigate to="/dashboard" replace />} />
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
        <Route path="/brain-training" element={<BrainTraining />} />
        <Route path="/pagt" element={<PilotDeferredPage title="Pan-Africa’s Got Talent is deferred for pilot" />} />
        <Route path="/membership" element={<MembershipOverviewPage />} />
        <Route path="/membership/community" element={<CommunityMembershipPage />} />
        <Route path="/membership/builder" element={<BuilderMembershipPage />} />
        <Route path="/billing/success" element={<BillingSuccessPage />} />
        <Route path="/billing/cancel" element={<BillingCancelPage />} />
        <Route path="/leadership" element={<LeadershipAssessmentPage />} />
        <Route path="/results" element={<LeadershipResultsPage />} />
        <Route path="/ops/verification" element={<SystemVerificationPage />} />
        <Route path="/debug/auth" element={<AuthDebugPage authChecked={authChecked} user={user} rbac={rbac} />} />
        <Route path="/decolonize" element={<Navigate to="/library" replace />} />
        <Route path="/library" element={<LibraryDecolonize canAccessOrganizer={canAccessOrganizer} authChecked={authChecked} user={user} />} />
        <Route
          path="/library/organizer"
          element={
            <OrganizerRoute
              authChecked={authChecked}
              user={user}
              rbac={rbac}
              canAccessOrganizer={canAccessOrganizer}
            />
          }
        />
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
  const [auth, setAuth] = useState({ user: null, rbac: { roles: [], permissions: [] } });
  const [authChecked, setAuthChecked] = useState(false);
  const user = auth.user;
  const rbac = auth.rbac;

  const refreshAuth = useCallback(async () => {
    try {
      if (API_DEBUG) {
        console.info("[runtime] auth/me request path", "/auth/me");
      }
      const data = await api("/auth/me", { method: "GET", headers: { Accept: "application/json" } });
      setAuth({
        user: data?.user || null,
        rbac: data?.rbac || { roles: [], permissions: [] },
      });
    } catch {
      setAuth({ user: null, rbac: { roles: [], permissions: [] } });
    } finally {
      setAuthChecked(true);
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const isAdmin = useMemo(() => isAdminUser(user, rbac), [user, rbac]);

  const canAccessOrganizer = useMemo(
    () => canAccessTextBookOrganizer(user, rbac, ENABLE_TEXT_BOOK_ORGANIZER, authChecked),
    [user, rbac, authChecked, ENABLE_TEXT_BOOK_ORGANIZER],
  );

  useEffect(() => {
    if (!AUTH_DEBUG) return;

    const roles = Array.isArray(rbac?.roles) ? rbac.roles : [];
    const permissions = Array.isArray(rbac?.permissions) ? rbac.permissions : [];

    console.info("[auth-debug] auth access state", {
      authChecked,
      email: user?.email || null,
      role: user?.role || null,
      roles,
      permissionCount: permissions.length,
      isAdmin,
      canAccessOrganizer,
    });
  }, [authChecked, user, rbac, isAdmin, canAccessOrganizer]);

  return (
    <Router>
      <CosmicBackgroundLayer />
      <AppRoutes
        user={user}
        rbac={rbac}
        isAdmin={isAdmin}
        canAccessOrganizer={canAccessOrganizer}
        authChecked={authChecked}
        refreshAuth={refreshAuth}
      />
    </Router>
  );
}
