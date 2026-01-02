import React from 'react';

export default function ActionConsole({ onShare, onReview, onRefresh, loading }) {
  return (
    <div className="action-console">
      <button
        disabled={loading}
        onClick={onShare}
        aria-label="Log a Share"
      >
        Log a Share
      </button>
      <button
        disabled={loading}
        onClick={onReview}
        aria-label="Submit Review Video"
      >
        Submit Review Video
      </button>
      <button
        disabled={loading}
        onClick={onRefresh}
        aria-label="Refresh Balance"
      >
        Refresh Balance
      </button>
    </div>
  );
}
