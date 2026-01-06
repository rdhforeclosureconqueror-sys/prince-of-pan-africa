import React, { useRef, useState } from "react";
import { speakMufasa } from "../utils/mufasaVoice";
import "./FitnessPage.css";

const FitnessPage = () => {
  const videoRef = useRef(null);
  const [status, setStatus] = useState("Camera not connected");
  const [isFull, setIsFull] = useState(false);

  // --- Backend URLs (direct setup) ---
  const NODE_URL = "https://mufasa-fitness-node.onrender.com";

  // --- Connect Camera ---
  async function connectCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
      setStatus("✅ Camera connected.");
      await speakMufasa("Welcome to Mufasa Fitness. Camera is active.");
    } catch (err) {
      console.error(err);
      setStatus("❌ Camera access failed.");
      await speakMufasa("Unable to connect your camera. Please check your settings.");
    }
  }

  // --- Fullscreen Toggle ---
  const toggleFullScreen = () => {
    setIsFull(!isFull);
    if (!isFull) {
      speakMufasa("Switching to full screen workout mode.");
    } else {
      speakMufasa("Exiting full screen mode.");
    }
  };

  // --- Start Workout ---
  async function startWorkout() {
    setStatus("Loading workout AI...");
    await speakMufasa("Initializing Ma’at two point O fitness intelligence. Please stand centered and ready.");
    // here’s where pose detection or live rep counting logic will plug in
  }

  // --- Stop Workout ---
  async function stopWorkout() {
    setStatus("Workout stopped.");
    await speakMufasa("Workout complete. Excellent effort.");
  }

  // --- AI Greeting ---
  async function aiGreeting() {
    await speakMufasa("Karibu! Welcome to your personalized fitness session. Let’s unlock your Pan African potential.");
  }

  return (
    <div className={`fitness-page ${isFull ? "fullscreen" : ""}`}>
      <div className="fit-header">
        <h1 className="fit-title">🦁 Mufasa Fitness</h1>
        <p className="fit-subtitle">AI-powered holistic health by Ma’at 2.0</p>
      </div>

      <div className="video-container">
        <video ref={videoRef} autoPlay playsInline muted></video>
      </div>

      <div className="fit-buttons">
        <button onClick={connectCamera}>🎥 Connect Camera</button>
        <button onClick={startWorkout}>💪 Start Workout</button>
        <button onClick={stopWorkout}>⏹ Stop Workout</button>
        <button onClick={aiGreeting}>🦁 Greet Me</button>
        <button onClick={toggleFullScreen}>
          {isFull ? "↩ Exit Fullscreen" : "⛶ Fullscreen Mode"}
        </button>
      </div>

      <div className="fit-status">
        <p>{status}</p>
      </div>
    </div>
  );
};

export default FitnessPage;
