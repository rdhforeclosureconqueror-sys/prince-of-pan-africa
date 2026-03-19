import React, { useMemo, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL || "";

const CATEGORY_FIXES = {
  database: "Check DATABASE_URL, DB connectivity, and ensure migrations/init ran.",
  auth: "Confirm /auth/me returns user payload and seeded admin exists.",
  member: "Ensure users/member_profiles/activity_logs contain records and /member routes are registered.",
  leadership: "Verify assessment submit/results/analytics routes and DB write permissions.",
  admin_ai: "Ensure /admin/ai endpoints are mounted and returning JSON.",
  tts: "Confirm /chat/tts is registered and AIVOICE/OpenAI env vars are set.",
  fitness: "Verify MufasaCoach throttling constants and anti-spam logic remain enabled.",
  env: "Populate missing env vars in backend and frontend deployment settings.",
  cors_routes: "Update ALLOWED_ORIGINS/CORS_ALLOWED_ORIGINS and verify required routes are mounted.",
};

function StatusBadge({ ok }) {
  return <span style={{ fontWeight: 700, color: ok ? "#22c55e" : "#ef4444" }}>{ok ? "PASS" : "FAIL"}</span>;
}

export default function SystemVerificationPage() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  const categories = useMemo(() => {
    if (!report) return [];
    return Object.entries(report).filter(([key, value]) => key !== "ok" && value && typeof value === "object" && "ok" in value);
  }, [report]);

  async function runVerification() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/system/verification/full`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `Verification failed (${res.status})`);
      setReport(data);
    } catch (err) {
      setError(err.message || "Failed to run verification");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-dashboard">
      <h1>✅ Verification Center</h1>
      <p>Run a one-click system validation for backend readiness.</p>
      <button className="mode-toggle" onClick={runVerification} disabled={loading}>
        {loading ? "Running..." : "Run Full Verification"}
      </button>
      {error ? <p className="admin-error">⚠️ {error}</p> : null}

      {report ? (
        <>
          <h2 style={{ marginTop: 20 }}>
            Overall: <StatusBadge ok={!!report.ok} />
          </h2>

          <section className="cosmic-section">
            <h2>Category Results</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Recommended Fix</th>
                </tr>
              </thead>
              <tbody>
                {categories.map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td><StatusBadge ok={!!value.ok} /></td>
                    <td>{value.ok ? "—" : CATEGORY_FIXES[key] || "Check category details."}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="cosmic-section">
            <h2>Raw Verification JSON</h2>
            <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{JSON.stringify(report, null, 2)}</pre>
          </section>
        </>
      ) : null}
    </div>
  );
}
