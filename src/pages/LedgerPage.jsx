import { useEffect, useState } from "react";
import { api } from "../api/api";
import { API_BASE } from "../config";

export default function LedgerPage() {
  const [log, setLog] = useState([]);
  const [data, setData] = useState(null);

  const add = (line) => setLog((prev) => [...prev, line]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        add(`API_BASE = ${API_BASE}`);

        add("Calling /auth/me ...");
        const me = await api("/auth/me");
        add(`✅ /auth/me OK`);

        // ✅ Your server creates the session user like:
        // { provider:"google", googleId, displayName, email, photo }
        // So the canonical ID in DB should be googleId.
        const id = me?.user?.googleId || me?.user?.email;

        add(`Resolved id = ${id || "(missing)"}`);

        if (!id) {
          throw new Error("No id found. Expected me.user.googleId (or fallback to email).");
        }

        add(`Calling /ledger/balance/${encodeURIComponent(id)} ...`);
        const bal = await api(`/ledger/balance/${encodeURIComponent(id)}`);
        add(`✅ /ledger/balance OK`);

        if (!cancelled) setData({ me, bal });
      } catch (e) {
        const msg = e?.message || String(e);

        // Helpful special-case so you know if it's auth/cookie vs code/db
        if (msg.includes("LOGIN_REQUIRED") || msg.includes("401")) {
          add("❌ Not logged in (LOGIN_REQUIRED / 401). Try logging in again.");
        } else {
          add(`❌ ERROR: ${msg}`);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
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
