import { useEffect, useState } from "react";
import { api } from "../api/api";

export default function LedgerPage() {
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const me = await api("/auth/me");

        // Use a consistent member_id. Strongly recommend googleId.
        const memberId = me.user.googleId || me.user.email;

        // Your backend screenshot shows: GET /ledger/balance/:member_id
        const data = await api(`/ledger/balance/${encodeURIComponent(memberId)}`);
        setBalance(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div style={{ padding: 20 }}>Loading ledger…</div>;
  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Black Dollar Ledger</h2>
      <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(balance, null, 2)}</pre>
    </div>
  );
}
