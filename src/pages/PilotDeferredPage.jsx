import React from "react";

export default function PilotDeferredPage({ title = "Deferred for Pilot", detail }) {
  return (
    <main style={{ maxWidth: 860, margin: "0 auto", padding: "20px 16px", color: "#f4f1e8" }}>
      <h1 style={{ color: "#f5e6b3" }}>{title}</h1>
      <p style={{ marginTop: 10, opacity: 0.92 }}>
        This surface is intentionally outside the Phase 4 pilot promise and has been locked to
        protect end-to-end pilot reliability.
      </p>
      {detail ? (
        <p style={{ marginTop: 8, opacity: 0.8 }}>
          {detail}
        </p>
      ) : null}
    </main>
  );
}
