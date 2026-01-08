import React, { useState } from "react";

export default function SessionLogPanel({ logs = [] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`log-panel ${open ? "open" : ""}`}>
      <button className="toggle-btn" onClick={() => setOpen(!open)}>
        {open ? "🦁 Hide Log" : "🦁 Show Log"}
      </button>

      {open && (
        <div className="log-content">
          <h3>Session Log (Last 7 Days)</h3>
          <ul>
            {logs.length === 0 ? (
              <li>No logs yet…</li>
            ) : (
              logs.map((log, i) => (
                <li key={i}>
                  <span>[{log.time}]</span> {log.voice}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
