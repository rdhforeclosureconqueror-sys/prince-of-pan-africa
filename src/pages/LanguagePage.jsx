import React from "react";
import { useMvpActions } from "../hooks/useMvpActions";

export default function LanguagePage() {
  const { lastReward } = useMvpActions();

  return (
    <div className="mvp-page">
      <h1>🗣️ Language Practice</h1>
      <p>Select Language</p>
      <select defaultValue="swahili">
        <option value="swahili">Swahili</option>
        <option value="zulu">Zulu</option>
        <option value="yoruba">Yoruba</option>
      </select>
      <button disabled title="Pilot mode: endpoint not enabled yet">
        🎤 Log Practice
      </button>
      <p style={{ opacity: 0.8, marginTop: 10 }}>
        Language practice logging is temporarily disabled in pilot mode.
      </p>

      {lastReward && (
        <div className="reward-toast">
          {`⭐ +${lastReward.stars} | XP +${lastReward.xp}`}
        </div>
      )}
    </div>
  );
}
