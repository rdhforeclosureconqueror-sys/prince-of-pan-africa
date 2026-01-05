import React from "react";
import { useMvpActions } from "../hooks/useMvpActions";

export default function FitnessPage() {
  const { logWorkout, logWater, loading, lastReward } = useMvpActions();

  return (
    <div className="mvp-page">
      <h1>🏋️ Fitness Portal</h1>
      <button onClick={logWorkout} disabled={loading}>
        ✅ Log Workout
      </button>
      <button onClick={logWater} disabled={loading}>
        💧 Log Water
      </button>

      {lastReward && (
        <div className="reward-toast">
          {`🏆 +${lastReward.xp} XP • ⭐ +${lastReward.stars}`}
        </div>
      )}
    </div>
  );
}
