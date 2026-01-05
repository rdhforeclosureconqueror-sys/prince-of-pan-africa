// ✅ src/components/XPProgressOverlay.jsx
import { useState, useEffect } from "react";
import "../styles/xpOverlay.css";

export default function XPProgressOverlay({ xp }) {
  const [progress, setProgress] = useState(xp || 0);

  useEffect(() => {
    setProgress(xp);
  }, [xp]);

  return (
    <div className="xp-overlay">
      <div className="xp-bar">
        <div
          className="xp-fill"
          style={{ width: `${Math.min(progress, 100)}%` }}
        ></div>
      </div>
      <div className="xp-label">XP: {progress.toFixed(0)} / 100</div>
    </div>
  );
}
