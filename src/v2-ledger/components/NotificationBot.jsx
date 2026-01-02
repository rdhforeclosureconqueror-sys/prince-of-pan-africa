// src/v2-ledger/components/NotificationBot.jsx
import React, { useEffect, useRef, useState } from "react";
import { api } from "../../api/api"; // <-- same helper used elsewhere
import "../../v2-ledger/ledgerV2.css";

/**
 * SimbaBot – lightweight notification + reminder assistant.
 *  - Connects via WebSocket for instant STAR awards.
 *  - Falls back to polling /ledger/notifications.
 *  - Shows toast-style alerts.
 */

export default function NotificationBot() {
  const [toasts, setToasts] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    const poll = setInterval(fetchFallback, 60_000); // 1-min fallback poll
    return () => {
      clearInterval(poll);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
      const wsURL = `${wsProto}://${window.location.host.replace(
        "www.",
        ""
      )}/ws`;
      const ws = new WebSocket(wsURL);
      wsRef.current = ws;

      ws.onopen = () => console.log("🦁 SimbaBot connected to WS");
      ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === "star_award") {
          pushToast(msg.message);
        } else if (msg.type === "reminder") {
          pushToast(msg.message);
        }
      };
      ws.onclose = () => console.log("🔌 SimbaBot WS closed");
      ws.onerror = (err) => console.error("WS error:", err);
    } catch (e) {
      console.error("Failed WS connection:", e);
    }
  };

  const fetchFallback = async () => {
    try {
      const res = await api("/ledger/notifications");
      if (res?.ok && Array.isArray(res.items)) {
        res.items.forEach((n) => {
          pushToast(n.message);
        });
      }
    } catch (err) {
      console.warn("Notification poll failed:", err);
    }
  };

  const pushToast = (msg) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, msg }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  };

  return (
    <div className="simba-toast-container">
      {toasts.map((t) => (
        <div key={t.id} className="simba-toast">
          <span>{t.msg}</span>
        </div>
      ))}
    </div>
  );
}
