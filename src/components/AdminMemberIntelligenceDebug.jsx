import React from "react";

export default function AdminMemberIntelligenceDebug({ intelligence, isAdmin = false }) {
  if (!isAdmin || !intelligence) return null;
  return (
    <details className="library-card role-review-panel" data-testid="admin-member-intelligence-debug">
      <summary><strong>Admin Debug · Member Intelligence</strong></summary>
      {intelligence.isFallback ? <p><strong>Fallback reason:</strong> {intelligence.fallbackReason}</p> : null}
      <p><strong>Evidence sources:</strong></p>
      <ul>{(intelligence.evidence || []).map((item, index) => <li key={`${item.source || "evidence"}-${index}`}>{item.source || item.summary}</li>)}</ul>
      <p><strong>Confidence calculation:</strong> {intelligence.confidenceCalculation || "Unavailable"}</p>
      <pre>{JSON.stringify(intelligence.rawMemberIntelligence || intelligence, null, 2)}</pre>
    </details>
  );
}
