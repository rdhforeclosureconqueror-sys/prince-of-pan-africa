import { useEffect, useMemo } from "react";
import useLocalMemory from "../hooks/useLocalMemory";
import { getMonthlyHighlights } from "../data/blackHistoryFacts";

export default function CalendarPanel() {
  const currentMonth = useMemo(
    () => new Date().toLocaleString("default", { month: "long" }),
    []
  );

  const [historyData, setHistoryData] = useLocalMemory("monthlyHistory", {
    month: currentMonth,
    highlights: getMonthlyHighlights(currentMonth),
  });

  // Keep localStorage in sync when the real month changes
  useEffect(() => {
    const monthNow = new Date().toLocaleString("default", { month: "long" });

    // If month changed or highlights missing, refresh from facts file
    if (
      historyData?.month !== monthNow ||
      !Array.isArray(historyData?.highlights) ||
      historyData.highlights.length === 0
    ) {
      setHistoryData({
        month: monthNow,
        highlights: getMonthlyHighlights(monthNow),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const safeMonth = historyData?.month || currentMonth;
  const safeHighlights =
    Array.isArray(historyData?.highlights) && historyData.highlights.length
      ? historyData.highlights
      : getMonthlyHighlights(safeMonth);

  return (
    <div
      className="calendar-panel"
      style={{
        border: "1px solid rgba(214,178,94,.25)",
        borderRadius: 18,
        padding: 14,
        background: "rgba(0,0,0,.28)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
        <h2 style={{ margin: 0, color: "#f5e6b3", fontSize: 16 }}>
          {safeMonth} in Black History
        </h2>

        <button
          type="button"
          onClick={() =>
            setHistoryData({
              month: safeMonth,
              highlights: getMonthlyHighlights(safeMonth),
            })
          }
          style={{
            padding: "8px 10px",
            borderRadius: 12,
            border: "1px solid rgba(214,178,94,.45)",
            background: "rgba(0,0,0,.25)",
            color: "#f5e6b3",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 12,
          }}
          title="Refresh from facts file"
        >
          ↻ Refresh
        </button>
      </div>

      <ul style={{ margin: "10px 0 0", paddingLeft: 18 }}>
        {safeHighlights.map((item, i) => (
          <li key={i} style={{ color: "rgba(244,241,232,.92)", marginBottom: 8 }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
