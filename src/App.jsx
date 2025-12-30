// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LedgerPage from "./pages/LedgerPage";
import PagtPage from "./pages/PagtPage";
import LoginGate from "./components/LoginGate";

import MufasaShell from "./layouts/MufasaShell";
import Home from "./pages/Home";
import TimelinePage from "./pages/TimelinePage";
import CalendarPage from "./pages/CalendarPage";
import JournalPage from "./pages/JournalPage";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import MembershipPlan from "./pages/MembershipPlan";
import PortalDecolonize from "./pages/PortalDecolonize";

function App() {
  return (
    <BrowserRouter>
      {/* Everything is protected behind the human gate */}
      <LoginGate>
        <Routes>
          {/* Shell wraps all “main” pages */}
          <Route element={<MufasaShell />}>
            <Route index element={<Home />} />
            <Route path="timeline" element={<TimelinePage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="journal" element={<JournalPage />} />
            <Route path="library" element={<LibraryDecolonize />} />
            <Route path="membership" element={<MembershipPlan />} />
            <Route path="portal/decolonize" element={<PortalDecolonize />} />
            <Route path="ledger" element={<LedgerPage />} />
            <Route path="pagt" element={<PagtPage />} />
            {/* Safety: if someone hits a bad URL, send them home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </LoginGate>
    </BrowserRouter>
  );
}

export default App;
