import React from "react";
import { Link } from "react-router-dom";

const PHASES = [
  {
    id: "phase-1",
    title: "Phase I — Foundation (Days 1–5)",
    desc: "Knowledge of Self, nervous system regulation, and narrative audit basics.",
  },
  {
    id: "phase-2",
    title: "Phase II — Regional Systems (Days 6–12)",
    desc: "Reintegration through African-aligned body–breath–mind practices and context.",
  },
  {
    id: "phase-3",
    title: "Phase III — Power Pattern Audit (Days 13–18)",
    desc: "Track distortions: rename, moralize, sanitize, erase, launder attribution.",
  },
  {
    id: "phase-4",
    title: "Phase IV — Repair & Reconstruction (Days 19–24)",
    desc: "Rebuild living practice: ethics, community coherence, modern application.",
  },
  {
    id: "phase-5",
    title: "Phase V — Integration & Teaching (Days 25–30)",
    desc: "Turn learning into service: curriculum, family practice, community delivery.",
  },
];

export default function LibraryDecolonize() {
  return (
    <div style={{ padding: 18, color: "#f4f1e8" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h1 style={{ margin: 0, color: "#f5e6b3" }}>Decolonization Library</h1>
        <p style={{ marginTop: 8, opacity: 0.85 }}>
          5 phases → click into the portal when you’re ready to run the process.
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
            ▶ Start Decolonization Portal
          </Link>

          <Link
            to="/membership"
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
            📅 View 30-Day Plan
          </Link>
        </div>

        <div
          style={{
            marginTop: 16,
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          {PHASES.map((p) => (
            <div
              key={p.id}
              style={{
                textAlign: "left",
                padding: 14,
                borderRadius: 16,
                border: "1px solid rgba(214,178,94,.35)",
                background: "rgba(0,0,0,.35)",
              }}
            >
              <div style={{ fontWeight: 900 }}>{p.title}</div>
              <div style={{ marginTop: 6, opacity: 0.85, fontSize: 13 }}>
                {p.desc}
              </div>

              <div style={{ marginTop: 10 }}>
                <Link
                  to="/portal/decolonize"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "9px 12px",
                    borderRadius: 999,
                    border: "1px solid rgba(214,178,94,.35)",
                    color: "#f4f1e8",
                    textDecoration: "none",
                    fontWeight: 800,
                    background: "rgba(0,0,0,.25)",
                  }}
                >
                  Open Portal →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
