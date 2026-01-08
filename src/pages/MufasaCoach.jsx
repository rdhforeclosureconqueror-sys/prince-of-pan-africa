import React, { useEffect, useRef, useState } from "react";
import { initVoice, speak, listenForWakeWord } from "../utils/voiceCoach";
import { initPose, analyzePose } from "../utils/poseAnalyzer";
import SessionLogPanel from "../components/SessionLogPanel";

export default function MufasaCoach() {
  const [mode, setMode] = useState("yoga"); // yoga | fitness
  const [poseStatus, setPoseStatus] = useState("Loading...");
  const [logs, setLogs] = useState([]);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // ✅ initialize MoveNet + Voice
  useEffect(() => {
    async function start() {
      await initVoice(mode);
      const detector = await initPose(videoRef.current);
      speak(`Welcome back. ${mode === "yoga" ? "Let's begin your yoga session." : "Ready for a strong fitness workout!"}`);
      setPoseStatus("Active");

      listenForWakeWord(() => {
        speak("I'm listening — what would you like to work on?");
      });

      const ctx = canvasRef.current.getContext("2d");
      async function detectLoop() {
        const poses = await detector.estimatePoses(videoRef.current);
        const feedback = analyzePose(ctx, poses[0]);
        if (feedback) {
          setLogs((prev) => [...prev.slice(-99), feedback]); // keep 100 entries
          if (feedback.voice) speak(feedback.voice);
        }
        requestAnimationFrame(detectLoop);
      }
      detectLoop();
    }
    start();
  }, [mode]);

  return (
    <div className="coach-wrap">
      <video ref={videoRef} className="camera-feed" autoPlay playsInline muted />
      <canvas ref={canvasRef} className="pose-overlay"></canvas>

      <div className="top-bar">
        <button
          className="mode-toggle"
          onClick={() => setMode(mode === "yoga" ? "fitness" : "yoga")}
        >
          {mode === "yoga" ? "Switch to Fitness Mode" : "Switch to Yoga Mode"}
        </button>
        <div className="status">{poseStatus}</div>
      </div>

      <SessionLogPanel logs={logs} />
    </div>
  );
}
