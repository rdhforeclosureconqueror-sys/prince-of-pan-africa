// ✅ src/ai/movementModel.js
import * as tf from "@tensorflow/tfjs-node";
import { pool } from "../server.js";
import { notifyAI } from "../utils/aiNotifier.js";

/**
 * Simulates pose recognition and form scoring.
 * In production, integrate MoveNet or BlazePose.
 */
export async function analyzeMovement({ member_id, session_id, movement_type, poseData }) {
  try {
    // 🔹 Normalize & predict
    const input = tf.tensor(poseData);
    const normalized = input.div(tf.scalar(255));
    const avgConfidence = normalized.mean().dataSync()[0] * 100;

    // 🔹 Determine reps and accuracy (placeholder logic)
    const reps = Math.floor(poseData.length / 30); // 30 frames per rep
    const accuracy = Math.min(100, Math.round(avgConfidence));

    // 🔹 Save session
    await pool.query(
      `INSERT INTO ai_movement_sessions (member_id, session_id, movement_type, reps, accuracy)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (session_id)
       DO NOTHING;`,
      [member_id, session_id, movement_type, reps, accuracy]
    );

    // 🔹 Award stars or XP
    if (accuracy >= 80 && reps >= 5) {
      await pool.query(
        `INSERT INTO star_transactions (member_id, delta, reason)
         VALUES ($1, 1, 'High-Accuracy Movement Session')`,
        [member_id]
      );
    }

    // 🔹 Notify real-time
    notifyAI(member_id, {
      type: "movement_feedback",
      category: movement_type,
      message: `🏋️ ${reps} reps • ${accuracy}% accuracy (+${accuracy >= 80 ? "1⭐" : "0⭐"})`,
      score: accuracy,
      reps,
    });

    return { ok: true, accuracy, reps };
  } catch (err) {
    console.error("❌ Movement analysis error:", err);
    return { ok: false, error: err.message };
  }
}
