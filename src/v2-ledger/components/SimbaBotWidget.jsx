import React, { useEffect, useState } from "react";
import "./SimbaBotWidget.css";

export default function SimbaBotWidget({ memberId }) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!memberId) return;

    const wsUrl = import.meta.env.VITE_WS_URL || "wss://api.simbawaujamaa.com";
    const ws = new WebSocket(wsUrl.replace(/^http/, "ws"));

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: "register", member_id: memberId }));
      console.log("🦁 SimbaBot connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "ack") return;
        const msg = {
          id: Date.now(),
          text: data.message,
          type: data.type,
          created_at: new Date(),
        };
        setMessages((prev) => [msg, ...prev].slice(0, 5));
      } catch (err) {
        console.error("SimbaBot message error:", err);
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    // Fallback: Poll for missed notifications
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch("/ledger/notifications", { credentials: "include" });
        const json = await res.json();
        if (json.ok && json.items?.length) {
          const newMsgs = json.items.map((i) => ({
            id: i.id,
            text: i.message,
            type: i.category,
            created_at: new Date(i.created_at),
          }));
          setMessages((prev) => [...newMsgs, ...prev].slice(0, 5));
        }
      } catch (err) {
        console.error("SimbaBot fallback fetch failed:", err);
      }
    }, 30000);

    return () => {
      ws.close();
      clearInterval(pollInterval);
    };
  }, [memberId]);

  return (
    <div className="simba-bot-widget">
      <div className="simba-bot-header">
        <span role="img" aria-label="lion">🦁</span>
        <span>SimbaBot</span>
        <div className={`status ${connected ? "online" : "offline"}`}></div>
      </div>
      <div className="simba-bot-messages">
        {messages.length === 0 ? (
          <div className="simba-bot-empty">No new messages</div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`simba-bot-msg type-${m.type}`}>
              {m.text}
              <span className="time">
                {m.created_at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
