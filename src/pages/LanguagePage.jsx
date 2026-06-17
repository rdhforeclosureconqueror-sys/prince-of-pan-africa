import React, { useState } from "react";
import { useMvpActions } from "../hooks/useMvpActions";
import { recordParticipationActivity } from "../api/participation";

export default function LanguagePage() {
  const { lastReward } = useMvpActions();
  const [language, setLanguage] = useState("swahili");
  const [starNotice, setStarNotice] = useState("");
  async function logPractice() {
    const activityType = language === "yoruba" ? "yoruba_lesson_completed" : "swahili_lesson_completed";
    try {
      const response = await recordParticipationActivity(activityType, language, { language });
      setStarNotice(response?.duplicate ? response?.message : `⭐ +${response?.awarded_star ?? response?.activity?.star_award ?? 0} STAR Community Credits — progress saved. Current STAR: ${response?.participation?.star ?? "—"}. Rank: ${response?.participation?.current_rank ?? "Member"}.`);
    } catch {
      setStarNotice("Sign in to save STAR for language practice.");
    }
  }

  return (
    <div className="mvp-page">
      <h1>🗣️ Language Practice</h1>
      <p>Select Language</p>
      <select value={language} onChange={(event) => setLanguage(event.target.value)}>
        <option value="swahili">Swahili</option>
        <option value="zulu">Zulu</option>
        <option value="yoruba">Yoruba</option>
      </select>
      <button onClick={logPractice}>🎤 Complete Lesson · Earn STAR</button>
      {starNotice ? <p style={{ opacity: 0.9, marginTop: 10 }}>{starNotice}</p> : null}

      {lastReward && (
        <div className="reward-toast">
          {`⭐ +${lastReward.stars} | XP +${lastReward.xp}`}
        </div>
      )}
    </div>
  );
}
