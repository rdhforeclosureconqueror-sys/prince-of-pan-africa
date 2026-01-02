import React, { useState, Suspense } from 'react';
import './ledgerV2.css';

import IdentityPanel from './components/IdentityPanel';
import BalanceCore from './components/BalanceCore';
import ActionConsole from './components/ActionConsole';
import ActivityStream from './components/ActivityStream';
import SystemMessages from './components/SystemMessages';
import useLedgerData from './hooks/useLedgerData';

// Lazy-load modals for performance
const EarnStarModal = React.lazy(() => import('./components/EarnStarModal'));
const ReviewVideoModal = React.lazy(() => import('./components/ReviewVideoModal'));

export default function LedgerV2Page() {
  const { balance, loading, error, refreshBalance } = useLedgerData();
  const [showShareModal, setShowShareModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);

  return (
    <div className="ledgerV2-shell">
      <div className="ledgerV2-top">
        <IdentityPanel />
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
      <Suspense fallback={null}>
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
    </div>
  );
}
