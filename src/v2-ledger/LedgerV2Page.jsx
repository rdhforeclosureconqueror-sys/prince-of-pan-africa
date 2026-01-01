import { useEffect, useState } from "react";
import { ledgerV2Api } from "./apiClient";
import "./styles/ledgerV2.css";

export default function LedgerV2Page() {
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);
  const [bal, setBal] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setError("");
        const meRes = await ledgerV2Api.me();
        setMe(meRes?.user || null);

        const balRes = await ledgerV2Api.balance();
        setBal(balRes);
      } catch (e) {
        setError(e?.message || "Failed to load ledger.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="v2-wrap"><div className="v2-card">Loading ledger…</div></div>;
  }

  if (error) {
    return (
      <div className="v2-wrap">
        <div className="v2-card">
          <h2>Ledger</h2>
          <p className="v2-error">Error: {error}</p>
          <p className="v2-muted">
            If you’re not logged in, go back and sign in. If you are logged in,
            the API might be down or CORS/cookies are blocked.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="v2-wrap">
      <div className="v2-header">
        <div>
          <div className="v2-title">Black Dollar Ledger</div>
          <div className="v2-subtitle">
            Signed in as {me?.email || me?.displayName || "Member"}
          </div>
        </div>
      </div>

      <div className="v2-grid">
        <div className="v2-card">
          <div className="v2-label">Black Dollars</div>
          <div className="v2-value">{bal?.bd ?? 0}</div>
        </div>

        <div className="v2-card">
          <div className="v2-label">Stars</div>
          <div className="v2-value">{bal?.stars ?? 0}</div>
        </div>

        <div className="v2-card v2-wide">
          <div className="v2-label">Member ID</div>
          <div className="v2-mono">{bal?.member_id || "—"}</div>
        </div>
      </div>

      <div className="v2-card v2-wide">
        <div className="v2-label">Next</div>
        <div className="v2-muted">
          This is the safe V2 page. Dev can now build out:
          transactions, share tracking, review approvals, admin tools —
          without touching the old files.
        </div>
      </div>
    </div>
  );
}
