import React, { useEffect, useRef } from "react";
import Chart from "chart.js/auto";

export default function ProgressCharts() {
  const chartRef = useRef(null);

  useEffect(() => {
    const ctx = chartRef.current.getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
        datasets: [
          {
            label: "Workout Consistency",
            data: [2, 3, 4, 5, 4],
            borderWidth: 2,
          },
        ],
      },
      options: {
        scales: { y: { beginAtZero: true } },
      },
    });
  }, []);

  return (
    <div className="panel chart-panel">
      <h2>Progress Overview</h2>
      <canvas ref={chartRef}></canvas>
    </div>
  );
}
