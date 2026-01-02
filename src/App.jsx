// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginGate from "./components/LoginGate";
import MufasaShell from "./layouts/MufasaShell";

import Home from "./pages/Home";
import TimelinePage from "./pages/TimelinePage";
import CalendarPage from "./pages/CalendarPage";
import JournalPage from "./pages/JournalPage";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import MembershipPlan from "./pages/MembershipPlan";
import PortalDecolonize from "./pages/PortalDecolonize";
import LedgerPage from "./pages/LedgerPage";
import LedgerV2Page from "./v2-ledger/LedgerV2Page";
import PagtPage from "./pages/PagtPage";
import AdminDashboard from "./v2-admin/AdminDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <LoginGate>
        <Routes>
          <Route element={<MufasaShell />}>
            <Route index element={<Home />} />
            <Route path="timeline" element={<TimelinePage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="journal" element={<JournalPage />} />
            <Route path="library" element={<LibraryDecolonize />} />
            <Route path="membership" element={<MembershipPlan />} />
            <Route path="portal/decolonize" element={<PortalDecolonize />} />
            <Route path="ledger" element={<LedgerPage />} />
            <Route path="ledger-v2" element={<LedgerV2Page />} />
            <Route path="pagt" element={<PagtPage />} />
            <Route path="admin" element={<AdminDashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </LoginGate>
    </BrowserRouter>
  );
}
