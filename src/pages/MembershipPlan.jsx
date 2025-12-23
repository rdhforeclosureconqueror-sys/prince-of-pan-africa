import React from "react";
import { Link } from "react-router-dom";

export default function MembershipPlan() {
  return (
    <div style={{ padding: 18, color: "#f4f1e8" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h1 style={{ margin: 0, color: "#f5e6b3" }}>30-Day Decolonization Plan</h1>
        <p style={{ marginTop: 8, opacity: 0.85 }}>
          This replaces “Membership” for now. Next step: we’ll paste your exact 5-phase + 30-day structure
          into a data file and render it day-by-day with resume codes.
        </p>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
          <Link
            to="/portal/decolonize"
            style={{
              padding: "10px 14px",
              borderRadius: 999,
              border: "1px solid rgba(16,185,129,.55)",
              background: "rgba(0,0,0,.25)",
              color: "#f4f1e8",
              textDecoration: "none",
              fontWeight: 800,
            }}
          >
            ▶ Run the Portal
          </Link>

          <Link
            to="/library"
            style={{
              padding: "10px 14px",
              borderRadius: 999,
              border: "1px solid rgba(214,178,94,.55)",
              background: "rgba(0,0,0,.25)",
              color: "#f4f1e8",
              textDecoration: "none",
              fontWeight: 800,
            }}
          >
            ← Back to Phases
          </Link>
        </div>

        <div
          style={{
            marginTop: 16,
            padding: 14,
            borderRadius: 16,
            border: "1px solid rgba(214,178,94,.35)",
            background: "rgba(0,0,0,.35)",
            lineHeight: 1.7,
            opacity: 0.92,
          }}
        >
          <b>Quick structure (placeholder until you paste your exact plan):</b>
          <ul>
            <li>Days 1–5: Foundation</li>
            <li>Days 6–12: Regional Systems</li>
            <li>Days 13–18: Power Pattern Audit</li>
            <li>Days 19–24: Repair & Reconstruction</li>
            <li>Days 25–30: Integration & Teaching</li>
          </ul>

          <div style={{ marginTop: 10, fontSize: 13, opacity: 0.85 }}>
            Next: we’ll turn your real plan into a structured dataset so the portal can load Day N,
            show the reading + practice, and (optionally) speak it with AI voice.
          </div>
        </div>
      </div>
    </div>
  );
}
