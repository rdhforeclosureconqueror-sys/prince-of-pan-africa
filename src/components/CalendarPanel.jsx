// ✅ src/components/CalendarPanel.jsx
import { useEffect, useMemo } from "react";
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

  // ✅ Sync when month changes (or if storage is empty/corrupt)
  useEffect(() => {
    const current = new Date().toLocaleString("default", { month: "long" });

    const needsRefresh =
      historyData?.month !== current ||
      !Array.isArray(historyData?.highlights) ||
      historyData.highlights.length === 0;

    if (needsRefresh) {
      setHistoryData({
        month: current,
        highlights: getMonthlyHighlights(current),
      });
    }
    // we intentionally do NOT depend on historyData to avoid loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setHistoryData]);

  const safeMonth = historyData?.month || monthNow;
  const safeHighlights = Array.isArray(historyData?.highlights) && historyData.highlights.length
    ? historyData.highlights
    : getMonthlyHighlights(safeMonth);

  const handleRefresh = () => {
    const current = new Date().toLocaleString("default", { month: "long" });
    setHistoryData({
      month: current,
      highlights: getMonthlyHighlights(current),
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
        maxWidth: 900,
        margin: "0 auto",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
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
            fontWeight: 600,
            fontSize: 12,
          }}
          title="Refresh from facts file"
        >
          ↻ Refresh
        </button>
      </div>

      <ul style={{ margin: "12px 0 0", paddingLeft: 18 }}>
        {safeHighlights.map((item, i) => (
          <li key={i} style={{ color: "rgba(244,241,232,.92)", marginBottom: 8, lineHeight: 1.45 }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
