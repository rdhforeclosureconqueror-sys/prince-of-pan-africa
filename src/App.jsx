import React, { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
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
import StarRewardsPage from "./pages/StarRewardsPage";
import ApplicationsPage from "./pages/ApplicationsPage";
import SystemVerificationPage from "./pages/SystemVerificationPage";
import AuthDebugPage from "./pages/AuthDebugPage";
import AssessmentLandingPage, { AssessmentCenter, AssessmentResultPage } from "./pages/AssessmentCenter";
import PilotDeferredPage from "./pages/PilotDeferredPage";
import StudyPage from "./pages/StudyPage";
import BrainTraining from "./pages/BrainTraining";
import { BuilderMembershipPage, CommunityMembershipPage, MembershipOverviewPage } from "./pages/MembershipPages";
import { BillingCancelPage, BillingSuccessPage } from "./pages/BillingStatusPages";
import BuilderOnboardingPage from "./pages/BuilderOnboardingPage";
import CommunityOnboardingPage from "./pages/CommunityOnboardingPage";
import CommunityDirectoryPage from "./pages/CommunityDirectoryPage";
import CommunityPreparednessPage from "./pages/CommunityPreparednessPage";
import MutualAidOverviewPage from "./pages/MutualAidOverviewPage";
import MutualAidAdminPlanningPage from "./pages/MutualAidAdminPlanningPage";
import MutualAidPilotReadinessPage from "./pages/MutualAidPilotReadinessPage";
import MutualAidAllowlistPreviewPage from "./pages/MutualAidAllowlistPreviewPage";
import MutualAidOperationsDashboard from "./pages/MutualAidOperationsDashboard";
import {
  MutualAidDisbursementsPreviewPage,
  MutualAidNominatePreviewPage,
  MutualAidReportsPreviewPage,
  MutualAidRequestPreviewPage,
  MutualAidRequestsPreviewPage,
  MutualAidReviewPreviewPage,
} from "./pages/MutualAidPilotPreviews";
import { getBackgroundForPath } from "./utils/backgroundSystem";
import { API_DEBUG, AUTH_DEBUG, ENABLE_MUTUAL_AID_ADMIN_PLANNING, ENABLE_MUTUAL_AID_ALLOWLIST_SHELL, ENABLE_MUTUAL_AID_OPERATIONS_DASHBOARD, ENABLE_MUTUAL_AID_OVERVIEW, ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL, ENABLE_MUTUAL_AID_PILOT_UI_SHELL, ENABLE_TEXT_BOOK_ORGANIZER } from "./config";
import { api } from "./api/api";
import { canAccessTextBookOrganizer, isAdminUser } from "./authz";
import "./styles/backgroundSystem.css";

function DashboardRoute({ authChecked, user, rbac, isAdmin }) {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.hash === "#star-rewards") {
      navigate("/star-rewards", { replace: true });
    }
  }, [location.hash, navigate]);

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

function shareVisitorId() {
  const key = "swu_visitor_id";
  let id = window.localStorage?.getItem(key);
  if (!id) {
    id = `visitor-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    window.localStorage?.setItem(key, id);
  }
  return id;
}

function ShareClickTracker() {
  const location = useLocation();

  useEffect(() => {
    const shareId = new URLSearchParams(location.search).get("swu_share");
    if (!shareId) return;
    api(`/audiobooks/shares/${shareId}/click`, {
      method: "POST",
      body: JSON.stringify({ visitor_id: shareVisitorId() }),
    }).catch((err) => {
      console.info("[share-tracking] click was not recorded", err);
    });
  }, [location.search]);

  return null;
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

function AdminPlanningRoute({ authChecked, user, isAdmin }) {
  if (!ENABLE_MUTUAL_AID_ADMIN_PLANNING) {
    return <PilotDeferredPage title="Mutual Aid admin planning is not enabled" />;
  }

  if (!authChecked) return <div className="admin-loading">Checking admin access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (!isAdmin) {
    return (
      <PilotDeferredPage
        title="Admin access required"
        detail="This internal Mutual Aid planning scaffold is available only to admin users."
      />
    );
  }

  return <MutualAidAdminPlanningPage />;
}

function AdminPilotReadinessRoute({ authChecked, user, isAdmin }) {
  if (!ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL) {
    return <PilotDeferredPage title="Mutual Aid pilot readiness shell is not enabled" />;
  }

  if (!authChecked) return <div className="admin-loading">Checking admin access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (!isAdmin) {
    return (
      <PilotDeferredPage
        title="Admin access required"
        detail="This static Mutual Aid pilot readiness shell is available only to admin users."
      />
    );
  }

  return <MutualAidPilotReadinessPage />;
}

function AdminAllowlistPreviewRoute({ authChecked, user, isAdmin }) {
  if (!ENABLE_MUTUAL_AID_ALLOWLIST_SHELL) {
    return <PilotDeferredPage title="Mutual Aid allowlist shell is not enabled" />;
  }

  if (!authChecked) return <div className="admin-loading">Checking admin access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (!isAdmin) {
    return (
      <PilotDeferredPage
        title="Admin access required"
        detail="This static Mutual Aid allowlist pilot access shell is available only to admin users."
      />
    );
  }

  return <MutualAidAllowlistPreviewPage />;
}

function AdminMutualAidOperationsDashboardRoute({ authChecked, user, isAdmin }) {
  if (!authChecked) return <div className="admin-loading">Checking admin access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (!isAdmin) {
    return (
      <PilotDeferredPage
        title="Admin access required"
        detail="This static Mutual Aid operations dashboard is available only to admin users."
      />
    );
  }

  return <MutualAidOperationsDashboard />;
}

function MutualAidPilotShellRoute({ children }) {
  if (!ENABLE_MUTUAL_AID_PILOT_UI_SHELL) {
    return <PilotDeferredPage title="Mutual Aid pilot UI shell is not enabled" />;
  }

  return children;
}

function AdminMutualAidPilotShellRoute({ authChecked, user, isAdmin, children }) {
  if (!ENABLE_MUTUAL_AID_PILOT_UI_SHELL) {
    return <PilotDeferredPage title="Mutual Aid pilot UI shell is not enabled" />;
  }

  if (!authChecked) return <div className="admin-loading">Checking admin access...</div>;
  if (!user) return <Navigate to="/?auth=login" replace />;
  if (!isAdmin) {
    return (
      <PilotDeferredPage
        title="Admin access required"
        detail="This preview-only Mutual Aid shell is available only to admin users."
      />
    );
  }

  return children;
}

function AppRoutes({ user, rbac, isAdmin, canAccessOrganizer, authChecked, refreshAuth }) {
  return (
    <>
      <GlobalNav user={user} rbac={rbac} canAccessOrganizer={canAccessOrganizer} authChecked={authChecked} />
      <ShareClickTracker />
      <Routes>
        <Route path="/" element={<Home user={user} isAdmin={isAdmin} canAccessOrganizer={canAccessOrganizer} authChecked={authChecked} onAuthChange={refreshAuth} />} />
        <Route path="/dashboard" element={<DashboardRoute authChecked={authChecked} user={user} rbac={rbac} isAdmin={isAdmin} />} />
        <Route path="/star-rewards" element={<StarRewardsPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/admin" element={<Navigate to="/dashboard" replace />} />
        <Route path="/admin/mutual-aid" element={<AdminPlanningRoute authChecked={authChecked} user={user} isAdmin={isAdmin} />} />
        <Route path="/admin/mutual-aid/pilot-readiness" element={<AdminPilotReadinessRoute authChecked={authChecked} user={user} isAdmin={isAdmin} />} />
        <Route path="/admin/mutual-aid/allowlist-preview" element={<AdminAllowlistPreviewRoute authChecked={authChecked} user={user} isAdmin={isAdmin} />} />
        {ENABLE_MUTUAL_AID_OPERATIONS_DASHBOARD ? (
          <Route path="/admin/mutual-aid/dashboard" element={<AdminMutualAidOperationsDashboardRoute authChecked={authChecked} user={user} isAdmin={isAdmin} />} />
        ) : null}
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
        <Route path="/builder/onboarding" element={<BuilderOnboardingPage />} />
        <Route path="/community/onboarding" element={<CommunityOnboardingPage />} />
        <Route path="/community/directory" element={<CommunityDirectoryPage />} />
        <Route path="/community/preparedness" element={<CommunityPreparednessPage />} />
        <Route
          path="/mutual-aid"
          element={
            ENABLE_MUTUAL_AID_OVERVIEW ? (
              <MutualAidOverviewPage />
            ) : (
              <PilotDeferredPage title="Mutual Aid overview is not enabled" />
            )
          }
        />

        <Route path="/mutual-aid/request-preview" element={<MutualAidPilotShellRoute><MutualAidRequestPreviewPage /></MutualAidPilotShellRoute>} />
        <Route path="/mutual-aid/nominate-preview" element={<MutualAidPilotShellRoute><MutualAidNominatePreviewPage /></MutualAidPilotShellRoute>} />
        <Route path="/mutual-aid/requests-preview" element={<MutualAidPilotShellRoute><MutualAidRequestsPreviewPage /></MutualAidPilotShellRoute>} />
        <Route path="/admin/mutual-aid/review-preview" element={<AdminMutualAidPilotShellRoute authChecked={authChecked} user={user} isAdmin={isAdmin}><MutualAidReviewPreviewPage /></AdminMutualAidPilotShellRoute>} />
        <Route path="/admin/mutual-aid/disbursements-preview" element={<AdminMutualAidPilotShellRoute authChecked={authChecked} user={user} isAdmin={isAdmin}><MutualAidDisbursementsPreviewPage /></AdminMutualAidPilotShellRoute>} />
        <Route path="/admin/mutual-aid/reports-preview" element={<AdminMutualAidPilotShellRoute authChecked={authChecked} user={user} isAdmin={isAdmin}><MutualAidReportsPreviewPage /></AdminMutualAidPilotShellRoute>} />
        <Route path="/preparedness" element={<Navigate to="/community/preparedness" replace />} />
        <Route path="/billing/cancel" element={<BillingCancelPage />} />
        <Route path="/assessments" element={<AssessmentLandingPage />} />
        <Route path="/assessments/center" element={<AssessmentCenter />} />
        <Route path="/assessments/results/:resultId" element={<AssessmentResultPage />} />
        <Route path="/leadership" element={<Navigate to="/assessments" replace />} />
        <Route path="/results" element={<Navigate to="/assessments" replace />} />
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
