// ✅ src/App.jsx — Simba Frontend Unified Entry
import React, { useEffect, useState, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

// 🧱 Core Layouts & Components
import LoginGate from "./components/LoginGate";
import MufasaShell from "./layouts/MufasaShell";

// 🧭 Main Pages
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
import AdminDashboard from "./pages/AdminDashboard";

// 🧠 Contexts / Utilities (WebSocket, Notifications)
import { toast } from "react-hot-toast";

export default function App() {
  const [user, setUser] = useState(null);
  const wsRef = useRef(null);

  // -----------------------------------------------
  // 🔗 1️⃣ WebSocket Connection (Realtime Engine)
  // -----------------------------------------------
  useEffect(() => {
    if (!user) return;

    const ws = new WebSocket(import.meta.env.VITE_WS_URL || "wss://simbawaujamaa.com");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("🟢 WebSocket connected");
      ws.send(JSON.stringify({
        type: user.role === "admin" ? "admin_register" : "register",
        member_id: user.id,
        role: user.role,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "reward_update":
            toast.success(`🏆 +${data.xp} XP • ⭐ +${data.stars}`);
            break;
          case "star_award":
            toast(`⭐ ${data.message}`, { icon: "🌟" });
            break;
          case "reminder":
            toast.info(data.message);
            break;
          case "member_activity":
            if (user.role === "admin") console.log("🧠 Admin Activity:", data);
            break;
          default:
            console.log("🔹 WS:", data);
        }
      } catch (e) {
        console.error("⚠️ WebSocket message error:", e);
      }
    };

    ws.onclose = () => console.log("🔴 WebSocket disconnected");
    return () => ws.close();
  }, [user]);

  // -----------------------------------------------
  // 🔒 2️⃣ Authentication Handling
  // -----------------------------------------------
  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await fetch("/auth/me", { credentials: "include" });
        const data = await res.json();
        if (data.ok) setUser(data.user);
      } catch (err) {
        console.error("❌ Auth check failed:", err);
      }
    }
    fetchUser();
  }, []);

  // -----------------------------------------------
  // 🧭 3️⃣ Router Structure
  // -----------------------------------------------
  return (
    <BrowserRouter>
      <LoginGate user={user}>
        <Routes>
          <Route element={<MufasaShell user={user} />}>
            {/* 🌍 Core Member Pages */}
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

            {/* 🧠 AI-Enhanced Phases */}
            <Route path="fitness" element={<JournalPage section="fitness" />} />
            <Route path="study" element={<JournalPage section="study" />} />
            <Route path="language" element={<JournalPage section="language" />} />

            {/* 🦁 Admin Galaxy Panel */}
            {user?.role === "admin" && (
              <Route path="admin" element={<AdminDashboard />} />
            )}

            {/* 🚧 Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </LoginGate>
    </BrowserRouter>
  );
}
