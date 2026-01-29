import React, { useMemo } from "react";

export default function ProgressCharts() {
  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const values = [2, 3, 4, 5, 4];
  const maxValue = Math.max(...values);

  const points = useMemo(() => {
    return values
      .map((value, index) => {
        const x = 10 + (index / (values.length - 1)) * 240;
        const y = 100 - (value / maxValue) * 80;
        return `${x},${y}`;
      })
      .join(" ");
  }, [values, maxValue]);

  return (
    <div className="panel chart-panel">
      <h2>Progress Overview</h2>
      <svg viewBox="0 0 260 120" role="img" aria-label="Workout consistency chart">
        <polyline
          points={points}
          fill="none"
          stroke="#ffd700"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {values.map((value, index) => {
          const x = 10 + (index / (values.length - 1)) * 240;
          const y = 100 - (value / maxValue) * 80;
          return <circle key={labels[index]} cx={x} cy={y} r="4" fill="#00ff88" />;
        })}
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        {labels.map((label) => (
          <span key={label} style={{ fontSize: 12, opacity: 0.75 }}>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
