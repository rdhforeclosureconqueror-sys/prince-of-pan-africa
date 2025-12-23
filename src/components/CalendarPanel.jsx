// src/components/CalendarPanel.jsx
import React, { useEffect, useMemo } from "react";
import useLocalMemory from "../hooks/useLocalMemory";
import { getMonthlyHighlights } from "../data/blackHistoryFacts";

export default function CalendarPanel() {
  const monthNow = useMemo(
    () => new Date().toLocaleString("default", { month: "long" }),
    []
  );

  const [historyData, setHistoryData] = useLocalMemory("monthlyHistory", {
    month: monthNow,
    highlights: getMonthlyHighlights(monthNow),
  });

  // Update if real month changed OR data is missing/bad
  useEffect(() => {
    const realMonth = new Date().toLocaleString("default", { month: "long" });

    const invalid =
      !historyData ||
      historyData.month !== realMonth ||
      !Array.isArray(historyData.highlights) ||
      historyData.highlights.length === 0;

    if (invalid) {
      setHistoryData({
        month: realMonth,
        highlights: getMonthlyHighlights(realMonth),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const safeMonth = historyData?.month || monthNow;

  const safeHighlights =
    Array.isArray(historyData?.highlights) && historyData.highlights.length
      ? historyData.highlights
      : getMonthlyHighlights(safeMonth);

  const handleRefresh = () => {
    setHistoryData({
      month: safeMonth,
      highlights: getMonthlyHighlights(safeMonth),
    });
  };

  return (
    <div
      className="calendar-panel"
      style={{
        border: "1px solid rgba(214,178,94,.25)",
        borderRadius: 18,
        padding: 16,
        background: "rgba(0,0,0,.28)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
        <h2 style={{ margin: 0, color: "#f5e6b3", fontSize: 16 }}>
          {safeMonth} in Black History
        </h2>

        <button
          type="button"
          onClick={handleRefresh}
          style={{
            padding: "8px 10px",
            borderRadius: 12,
            border: "1px solid rgba(214,178,94,.45)",
            background: "rgba(0,0,0,.25)",
            color: "#f5e6b3",
            cursor: "pointer",
            fontWeight: 700,
            fontSize: 12,
          }}
          title="Refresh from facts file"
        >
          ↻ Refresh
        </button>
      </div>

      <ul style={{ margin: "12px 0 0", paddingLeft: 18 }}>
        {safeHighlights.map((item, i) => (
          <li
            key={i}
            style={{
              color: "rgba(244,241,232,.92)",
              marginBottom: 10,
              lineHeight: 1.35,
            }}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
