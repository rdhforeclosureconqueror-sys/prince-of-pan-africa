import { useEffect, useState } from "react";
import { api } from "../api/api";
import { API_BASE } from "../config";

export default function LedgerPage() {
  const [log, setLog] = useState([]);
  const [data, setData] = useState(null);

  function add(line) {
    setLog((prev) => [...prev, line]);
  }

  useEffect(() => {
    (async () => {
      try {
        add(`API_BASE = ${API_BASE}`);

        add("Calling /auth/me ...");
        const me = await api("/auth/me");
        add(`✅ /auth/me OK: ${JSON.stringify(me)}`);

        const memberId = me?.user?.googleId || me?.user?.email;
        add(`memberId = ${memberId}`);

        add("Calling /ledger/balance/:memberId ...");
        const bal = await api(`/ledger/balance/${encodeURIComponent(memberId)}`);
        add(`✅ Ledger OK: ${JSON.stringify(bal)}`);
        setData({ me, bal });
      } catch (e) {
        add(`❌ ERROR: ${e.message}`);
      }
    })();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2>Black Dollar Ledger</h2>

      <div style={{ marginTop: 12, padding: 12, border: "1px solid #333" }}>
        <strong>Debug Log</strong>
        <pre style={{ whiteSpace: "pre-wrap" }}>{log.join("\n")}</pre>
      </div>

      {data && (
        <div style={{ marginTop: 12 }}>
          <strong>Data</strong>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
