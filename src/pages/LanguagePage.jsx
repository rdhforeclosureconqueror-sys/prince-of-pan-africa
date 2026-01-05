import React, { useState } from "react";
import { useMvpActions } from "../hooks/useMvpActions";

export default function LanguagePage() {
  const { logLanguagePractice, lastReward } = useMvpActions();
  const [languageKey, setLanguageKey] = useState("swahili");

  return (
    <div className="mvp-page">
      <h1>🗣️ Language Practice</h1>
      <p>Select Language</p>
      <select onChange={(e) => setLanguageKey(e.target.value)}>
        <option value="swahili">Swahili</option>
        <option value="zulu">Zulu</option>
        <option value="yoruba">Yoruba</option>
      </select>
      <button
        onClick={() => logLanguagePractice(languageKey, ["voice1.mp3", "voice2.mp3"])}
      >
        🎤 Log Practice
      </button>

      {lastReward && (
        <div className="reward-toast">
          {`⭐ +${lastReward.stars} | XP +${lastReward.xp}`}
        </div>
      )}
    </div>
  );
}
