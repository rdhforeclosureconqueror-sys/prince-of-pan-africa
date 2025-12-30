import { useState } from "react";
import { api } from "../api/api";

export default function PagtPage() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function testVote() {
    setError("");
    setResult(null);

    try {
      const me = await api("/auth/me");
      const member_id = me.user.googleId || me.user.email;

      // ⚠️ Match your actual voteSchema keys in pagtRoutes.js
      const payload = {
        member_id,
        contest_id: "demo-contest",
        contestant_id: "demo-contestant",
        votes: 1,
        pay_with: "free", // or "stars"
      };

      const data = await api("/pagt/vote", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setResult(data);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h2>Pan-Africa Got Talent</h2>
      <button onClick={testVote}>Test Vote</button>

      {error && <div style={{ marginTop: 10 }}>Error: {error}</div>}
      {result && <pre style={{ marginTop: 10 }}>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
