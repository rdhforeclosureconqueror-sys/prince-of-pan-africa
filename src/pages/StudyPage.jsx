import React, { useState } from "react";
import { useMvpActions } from "../hooks/useMvpActions";

export default function StudyPage() {
  const { addJournal, shareTopic, lastReward } = useMvpActions();
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
      <button onClick={() => addJournal(title, content)}>📝 Submit Journal</button>
      <button onClick={() => shareTopic(title)}>📤 Share Study</button>

      {lastReward && (
        <div className="reward-toast">
          {`⭐ +${lastReward.stars} | XP +${lastReward.xp}`}
        </div>
      )}
    </div>
  );
}
