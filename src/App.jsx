import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

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

// ===== Basic Navbar Component =====
const NavBar = () => {
  return (
    <nav className="bg-gray-900 text-white px-6 py-3 flex flex-wrap gap-4 items-center justify-center">
      <Link to="/" className="hover:text-yellow-400 font-semibold">Home</Link>
      <Link to="/dashboard" className="hover:text-yellow-400">Dashboard</Link>
      <Link to="/fitness" className="hover:text-yellow-400">Fitness</Link>
      <Link to="/study" className="hover:text-yellow-400">Study</Link>
      <Link to="/journal" className="hover:text-yellow-400">Journal</Link>
      <Link to="/language" className="hover:text-yellow-400">Language</Link>
      <Link to="/ledger" className="hover:text-yellow-400">Ledger</Link>
      <Link to="/library" className="hover:text-yellow-400">Library</Link>
      <Link to="/portal" className="hover:text-yellow-400">Portal</Link>
      <Link to="/timeline" className="hover:text-yellow-400">Timeline</Link>
      <Link to="/membership" className="hover:text-yellow-400">Membership</Link>
      <Link to="/admin" className="hover:text-yellow-400">Admin</Link>
      <Link to="/admin/ai" className="hover:text-yellow-400">AI Dashboard</Link>
    </nav>
  );
};

// ===== App.jsx Root =====
function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100 text-gray-900">
        {/* Navigation bar */}
        <NavBar />

        {/* Page Routes */}
        <Routes>
          <Route path="/" element={<Home />} />

          {/* Dashboards */}
          <Route path="/dashboard" element={<HolisticDashboard />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/ai" element={<AdminDashboardAI />} />

          {/* Functional Pages */}
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

          {/* Fallback route */}
          <Route
            path="*"
            element={
              <div className="p-8 text-center">
                <h1 className="text-3xl font-bold text-red-500 mb-4">404</h1>
                <p className="text-gray-600">
                  The page you’re looking for doesn’t exist.
                </p>
              </div>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
