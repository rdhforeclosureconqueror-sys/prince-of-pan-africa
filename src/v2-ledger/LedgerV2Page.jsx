import React, { useState, useEffect, Suspense } from "react";
import { API_BASE_URL } from "../config"; // ✅ import base URL
import "./ledgerV2.css";

import IdentityPanel from "./components/IdentityPanel";
import BalanceCore from "./components/BalanceCore";
import ActionConsole from "./components/ActionConsole";
import ActivityStream from "./components/ActivityStream";
import SystemMessages from "./components/SystemMessages";
import useLedgerData from "./hooks/useLedgerData";
import SimbaBotWidget from "./components/SimbaBotWidget";

// Lazy-load modals for performance
const EarnStarModal = React.lazy(() => import("./components/EarnStarModal"));
const ReviewVideoModal = React.lazy(() => import("./components/ReviewVideoModal"));

export default function LedgerV2Page() {
  const { balance, loading, error, refreshBalance } = useLedgerData();

  // Modal toggles
  const [showShareModal, setShowShareModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);

  // User state (for SimbaBot connection)
  const [memberId, setMemberId] = useState(null);
  const [user, setUser] = useState(null);

  // Fetch user info from backend
  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await fetch(`${API_BASE_URL}/auth/me`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.ok && data.auth) {
          setUser(data.user);
          setMemberId(data.user?.id || data.user?.member_id);
        } else {
          console.warn("Not authenticated:", data);
        }
      } catch (err) {
        console.error("Failed to fetch user info", err);
      }
    }
    fetchUser();
  }, []);

  return (
    <div className="ledgerV2-shell">
      <div className="ledgerV2-top">
        <IdentityPanel user={user} />
        <BalanceCore balance={balance} loading={loading} />
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <ActionConsole
        onShare={() => setShowShareModal(true)}
        onReview={() => setShowReviewModal(true)}
        onRefresh={refreshBalance}
        loading={loading}
      />

      <ActivityStream />
      <SystemMessages />

      {/* Lazy-loaded modals */}
      <Suspense fallback={<div>Loading...</div>}>
        {showShareModal && (
          <EarnStarModal
            onClose={() => setShowShareModal(false)}
            onSuccess={refreshBalance}
          />
        )}
        {showReviewModal && (
          <ReviewVideoModal
            onClose={() => setShowReviewModal(false)}
            onSuccess={refreshBalance}
          />
        )}
      </Suspense>

      {/* 🦁 SimbaBot Widget */}
      {memberId && <SimbaBotWidget memberId={memberId} />}
    </div>
  );
}
