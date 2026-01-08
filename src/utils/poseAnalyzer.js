let ctx;

export async function initPose(video) {
  const detector = await poseDetection.createDetector(
    poseDetection.SupportedModels.MoveNet,
    { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
  );

  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480 },
  });
  video.srcObject = stream;
  await video.play();

  return detector;
}

// Draw and analyze pose
export function analyzePose(canvasCtx, pose) {
  if (!pose || !pose.keypoints) return null;
  ctx = canvasCtx;
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  let badParts = [];
  pose.keypoints.forEach((kp) => {
    if (kp.score > 0.4) {
      ctx.beginPath();
      ctx.arc(kp.x, kp.y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = kp.score > 0.75 ? "#00ff66" : "#ff4444";
      ctx.fill();
    }
  });

  // Simple posture analysis
  const leftShoulder = pose.keypoints.find((p) => p.name === "left_shoulder");
  const rightShoulder = pose.keypoints.find((p) => p.name === "right_shoulder");
  const leftKnee = pose.keypoints.find((p) => p.name === "left_knee");
  const rightKnee = pose.keypoints.find((p) => p.name === "right_knee");

  let feedback = null;

  if (leftShoulder && rightShoulder) {
    const shoulderDiff = Math.abs(leftShoulder.y - rightShoulder.y);
    if (shoulderDiff > 40) {
      badParts.push("Shoulders uneven");
      feedback = "Straighten your shoulders.";
    }
  }

  if (leftKnee && rightKnee) {
    const kneeDiff = Math.abs(leftKnee.y - rightKnee.y);
    if (kneeDiff > 60) {
      badParts.push("Knees misaligned");
      feedback = "Balance your stance evenly.";
    }
  }

  if (badParts.length === 0) {
    feedback = "Good form — keep breathing steady.";
  }

  return {
    time: new Date().toLocaleTimeString(),
    parts: badParts,
    voice: feedback,
  };
}
