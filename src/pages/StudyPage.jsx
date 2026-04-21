import React, { useState } from "react";
import { useMvpActions } from "../hooks/useMvpActions";

export default function StudyPage() {
  const { lastReward } = useMvpActions();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  return (
    <div className="mvp-page">
      <h1>📖 Study & Journaling</h1>
      <input
        placeholder="Journal Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        placeholder="Write your reflection..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
      <button disabled title="Pilot mode: endpoint not enabled yet">📝 Submit Journal</button>
      <button disabled title="Pilot mode: endpoint not enabled yet">📤 Share Study</button>
      <p style={{ opacity: 0.8, marginTop: 10 }}>
        Study submission is temporarily disabled in pilot mode while backend endpoints are finalized.
      </p>

      {lastReward && (
        <div className="reward-toast">
          {`⭐ +${lastReward.stars} | XP +${lastReward.xp}`}
        </div>
      )}
    </div>
  );
}
