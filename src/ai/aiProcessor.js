// ✅ Frontend: src/ai/aiProcessor.js
import * as tf from "@tensorflow/tfjs";

export async function calculateMotionAccuracy(motionData) {
  const input = tf.tensor(motionData);
  const normalized = input.div(tf.scalar(255));
  const intensity = (await normalized.mean().data())[0] * 100;
  const accuracy = Math.max(0, 100 - Math.abs(50 - intensity));
  return { intensity, accuracy };
}

export async function calculateVoiceClarity(audioFeatures) {
  const clarity = tf.tensor(audioFeatures).mean().dataSync()[0] * 100;
  return { clarity };
}

export function calculateJournalPositivity(content) {
  const positivity =
    (content.match(/(peace|growth|love|progress|power|heal|unity)/gi) || [])
      .length * 10;
  return { positivity };
}
