// src/pages/CalendarPage.jsx
import React from "react";
import CalendarPanel from "../components/CalendarPanel";

export default function CalendarPage() {
  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "18px 14px" }}>
      <CalendarPanel />
    </div>
  );
}
