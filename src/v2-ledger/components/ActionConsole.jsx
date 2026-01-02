import React from 'react';

export default function ActionConsole({ onShare, onReview, onRefresh, loading }) {
  return (
    <div className="action-console">
      <button disabled={loading} onClick={onShare}>Log a Share</button>
      <button disabled={loading} onClick={onReview}>Submit Review Video</button>
      <button disabled={loading} onClick={onRefresh}>Refresh Balance</button>
    </div>
  );
}
