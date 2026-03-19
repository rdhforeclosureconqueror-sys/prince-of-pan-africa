import React, { useEffect, useRef, useState } from "react";
import { initVoice, speak, listenForWakeWord } from "../utils/voiceCoach";
import { initPose, analyzePose } from "../utils/poseAnalyzer";
import SessionLogPanel from "../components/SessionLogPanel";
import "../styles/fitness.css";

const SPEAK_INTERVAL = 2000;

export default function MufasaCoach() {
  const [mode, setMode] = useState("yoga"); // yoga | fitness
  const [poseStatus, setPoseStatus] = useState("Loading...");
  const [logs, setLogs] = useState([]);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const lastSpokenRef = useRef(0);
  const lastMessageRef = useRef("");

  function throttledSpeak(message) {
    if (!message) return;
    const now = Date.now();
    if (message === lastMessageRef.current && now - lastSpokenRef.current < SPEAK_INTERVAL) return;
    if (now - lastSpokenRef.current < SPEAK_INTERVAL) return;

    lastMessageRef.current = message;
    lastSpokenRef.current = now;
    speak(message);
  }

  useEffect(() => {
    let mounted = true;
    let rafId;

    async function start() {
      await initVoice(mode);
      const detector = await initPose(videoRef.current);
      if (!mounted) return;

      throttledSpeak(
        `Welcome back. ${mode === "yoga" ? "Let's begin your yoga session." : "Ready for a strong fitness workout!"}`,
      );
      setPoseStatus("Active");

      listenForWakeWord(() => {
        throttledSpeak("I'm listening — what would you like to work on?");
      });

      const ctx = canvasRef.current.getContext("2d");
      async function detectLoop() {
        const poses = await detector.estimatePoses(videoRef.current);
        const feedback = analyzePose(ctx, poses[0]);
        if (feedback) {
          setLogs((prev) => [...prev.slice(-99), feedback]);
          if (feedback.voice) throttledSpeak(feedback.voice);
        }
        rafId = requestAnimationFrame(detectLoop);
      }
      detectLoop();
    }

    start();

    return () => {
      mounted = false;
      if (rafId) cancelAnimationFrame(rafId);
    };
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
