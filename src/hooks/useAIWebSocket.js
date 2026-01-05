// ✅ src/hooks/useAIWebSocket.js
import { useEffect } from "react";

export function useAIWebSocket(memberId, onMessage) {
  useEffect(() => {
    if (!memberId) return;
    const ws = new WebSocket("wss://api.simbawaujamaa.com");

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "register", member_id: memberId }));
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === "ai_feedback") {
          onMessage?.(data);
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    return () => ws.close();
  }, [memberId, onMessage]);
}
