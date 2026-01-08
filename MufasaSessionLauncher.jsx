import React from "react";

export default function MufasaSessionLauncher({ onLaunch }) {
  return (
    <div className="panel session-launcher">
      <h2>Start Training</h2>
      <p>When ready, activate your AI coach for real-time feedback.</p>
      <button className="start-btn" onClick={onLaunch}>
        Launch Mufasa Coach 🦁
      </button>
    </div>
  );
}
