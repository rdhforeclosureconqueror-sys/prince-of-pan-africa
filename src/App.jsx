// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LibraryDecolonize from "./pages/LibraryDecolonize";
import MembershipPlan from "./pages/MembershipPlan";

import MufasaShell from "./layouts/MufasaShell";
import Home from "./pages/Home";
import PortalDecolonize from "./pages/PortalDecolonize";
import TimelinePage from "./pages/TimelinePage";
import CalendarPage from "./pages/CalendarPage";
import JournalPage from "./pages/JournalPage";

function App() {
  return (
    <BrowserRouter>
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
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
