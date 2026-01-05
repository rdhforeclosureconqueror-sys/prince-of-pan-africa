// ✅ Example integration: src/pages/FitnessPage.jsx
import { useState } from "react";
import { useAIWebSocket } from "../hooks/useAIWebSocket";
import AchievementToast from "../components/AchievementToast";
import XPProgressOverlay from "../components/XPProgressOverlay";
import { playSound } from "../utils/playSound";

export default function FitnessPage({ user }) {
  const [feedback, setFeedback] = useState(null);
  const [xp, setXp] = useState(0);

  useAIWebSocket(user.id, (msg) => {
    if (msg.type === "ai_feedback") {
      setFeedback(msg);
      playSound("achievement");
      setXp((x) => Math.min(100, x + 10)); // add XP
    }
  });

  return (
    <>
      <div className="fitness-page">
        <h1>🏋️‍♂️ Simba Fitness Arena</h1>
        <p>Train, speak, study — grow stronger with every step.</p>
      </div>

      <AchievementToast feedback={feedback} />
      <XPProgressOverlay xp={xp} />
    </>
  );
}
