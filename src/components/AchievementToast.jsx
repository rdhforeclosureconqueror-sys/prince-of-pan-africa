// ✅ src/components/AchievementToast.jsx
import { useEffect, useState } from "react";
import "../styles/achievementToast.css";

export default function AchievementToast({ feedback }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (feedback) {
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [feedback]);

  if (!feedback || !visible) return null;

  const icons = {
    motion: "🏋️",
    voice: "🎤",
    journal: "📚",
    share: "🌍",
    default: "⭐",
  };

  return (
    <div className="achievement-toast">
      <div className="toast-icon">{icons[feedback.category] || icons.default}</div>
      <div className="toast-body">
        <div className="toast-title">Achievement Unlocked!</div>
        <div className="toast-message">{feedback.message}</div>
      </div>
    </div>
  );
}
