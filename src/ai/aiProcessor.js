// ✅ src/ai/movementProcessor.js
import * as tf from "@tensorflow/tfjs";

/**
 * Calculate accuracy and reps using pose data from MoveNet/BlazePose.
 */
export async function calculateMovementMetrics(poseData = []) {
  if (!poseData.length) return { accuracy: 0, reps: 0 };

  const input = tf.tensor(poseData);
  const normalized = input.div(tf.scalar(255));
  const avgConfidence = (await normalized.mean().data())[0] * 100;

  const reps = Math.floor(poseData.length / 30); // 30 frames per rep
  const accuracy = Math.min(100, Math.round(avgConfidence));

  return { accuracy, reps };
}
