import React, { useEffect, useRef, useState } from "react";
import "./FitnessPage.css";
import { speakMufasa } from "../utils/mufasaVoice"; // your existing voice utility

export default function FitnessPage() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [poses, setPoses] = useState([]);
  const [activePose, setActivePose] = useState(null);
  const [poseScore, setPoseScore] = useState(0);
  const [status, setStatus] = useState("Loading...");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  // TensorFlow MoveNet global vars
  const detectorRef = useRef(null);
  const rafRef = useRef(null);
  const prevFeedbackRef = useRef("");
  const lastSpeakTimeRef = useRef(0);

  // ---------------------------
  // INIT: load MoveNet + pose list
  // ---------------------------
  useEffect(() => {
    async function init() {
      await loadPoseList();
      await loadMoveNet();
      await startCamera();
      setupVoiceRecognition();
    }
    init();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  async function loadPoseList() {
    try {
      const res = await fetch("/yoga/index.json");
      const data = await res.json();
      setPoses(data);
      setActivePose(data[0]);
      setStatus("Ready to begin your yoga session.");
    } catch (err) {
      console.error(err);
      setStatus("Could not load yoga poses list.");
    }
  }

  async function loadMoveNet() {
    if (!window.poseDetection) {
      await loadScript("https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@3.21.0");
      await loadScript("https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection");
    }
    const detector = await window.poseDetection.createDetector(
      window.poseDetection.SupportedModels.MoveNet,
      { modelType: "SinglePose.Lightning" }
    );
    detectorRef.current = detector;
  }

  async function startCamera() {
    const video = videoRef.current;
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    await video.play();
    detectLoop();
  }

  async function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.body.appendChild(s);
    });
  }

  // ---------------------------
  // POSE DETECTION LOOP
  // ---------------------------
  async function detectLoop() {
    if (!detectorRef.current || !videoRef.current) return;
    const detector = detectorRef.current;
    const video = videoRef.current;
    const poses = await detector.estimatePoses(video);
    if (poses && poses.length > 0) drawPose(poses[0]);
    rafRef.current = requestAnimationFrame(detectLoop);
  }

  // ---------------------------
  // DRAW POSE SKELETON
  // ---------------------------
  function drawPose(pose) {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const keypoints = pose.keypoints;

    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#d6b25e";
    ctx.lineWidth = 3;
    ctx.fillStyle = "#ff3333";

    keypoints.forEach(kp => {
      if (kp.score > 0.4) {
        ctx.beginPath();
        ctx.arc(kp.x, kp.y, 5, 0, 2 * Math.PI);
        ctx.fill();
      }
    });

    // analyze form if active pose selected
    if (activePose) analyzePose(pose.keypoints);
  }

  // ---------------------------
  // ANGLE CALC + COMPARISON
  // ---------------------------
  async function analyzePose(keypoints) {
    const now = Date.now();
    const poseData = await loadPoseCSV(activePose.file);
    if (!poseData.length) return;

    const userAngles = calcAngles(keypoints);
    const avgPoseAngles = averagePose(poseData);

    const diff = comparePoses(userAngles, avgPoseAngles);
    setPoseScore(Math.max(0, 100 - diff * 100));

    // Real-time feedback with voice
    if (now - lastSpeakTimeRef.current > 4000) {
      const feedback = getVoiceFeedback(diff, userAngles, avgPoseAngles);
      if (feedback && feedback !== prevFeedbackRef.current) {
        speakMufasa(feedback);
        prevFeedbackRef.current = feedback;
        lastSpeakTimeRef.current = now;
      }
    }
  }

  async function loadPoseCSV(fileName) {
    try {
      const res = await fetch(`/yoga/datasets/${fileName}`);
      const text = await res.text();
      const rows = text.split("\n").slice(1);
      return rows
        .map(r => r.split(",").map(x => parseFloat(x)))
        .filter(r => r.every(v => !isNaN(v)));
    } catch {
      return [];
    }
  }

  function calcAngles(keypoints) {
    const get = name =>
      keypoints.find(k => k.name === name || k.part === name);
    const angle = (A, B, C) => {
      if (!A || !B || !C) return 0;
      const AB = [A.x - B.x, A.y - B.y];
      const CB = [C.x - B.x, C.y - B.y];
      const dot = AB[0] * CB[0] + AB[1] * CB[1];
      const magA = Math.sqrt(AB[0] ** 2 + AB[1] ** 2);
      const magB = Math.sqrt(CB[0] ** 2 + CB[1] ** 2);
      const cosine = dot / (magA * magB);
      return Math.acos(Math.min(Math.max(cosine, -1), 1)) * (180 / Math.PI);
    };
    return {
      leftElbow: angle(get("left_shoulder"), get("left_elbow"), get("left_wrist")),
      rightElbow: angle(get("right_shoulder"), get("right_elbow"), get("right_wrist")),
      leftKnee: angle(get("left_hip"), get("left_knee"), get("left_ankle")),
      rightKnee: angle(get("right_hip"), get("right_knee"), get("right_ankle")),
      leftHip: angle(get("left_shoulder"), get("left_hip"), get("left_knee")),
      rightHip: angle(get("right_shoulder"), get("right_hip"), get("right_knee")),
      spine: angle(get("left_shoulder"), get("left_hip"), get("right_hip")),
    };
  }

  function averagePose(data) {
    const avg = {};
    const cols = data[0].length;
    for (let i = 0; i < cols; i++) {
      const sum = data.reduce((a, b) => a + b[i], 0);
      avg[i] = sum / data.length;
    }
    return avg;
  }

  function comparePoses(user, ref) {
    const values = Object.values(user);
    const refValues = Object.values(ref).slice(0, values.length);
    const diff = values.reduce((sum, v, i) => sum + Math.abs(v - refValues[i]), 0);
    return diff / values.length / 180;
  }

  function getVoiceFeedback(diff, user, ref) {
    if (diff < 0.05) return "Perfect form! Hold it steady.";
    if (diff < 0.1) return "Almost there. Small adjustments.";
    if (diff < 0.2) return "Engage your core and realign your hips.";
    return "Reset your stance and find your balance.";
  }

  // ---------------------------
  // VOICE CONTROL / HANDS-FREE
  // ---------------------------
  function setupVoiceRecognition() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = false;
    rec.lang = "en-US";
    rec.onresult = e => {
      const text = e.results[e.results.length - 1][0].transcript.toLowerCase();
      if (text.includes("hey coach") || text.includes("mufasa")) {
        speakMufasa("Yes? I'm listening.");
        setListening(true);
      } else if (listening) handleVoiceCommand(text);
    };
    rec.start();
    recognitionRef.current = rec;
  }

  function handleVoiceCommand(cmd) {
    if (cmd.includes("next pose")) nextPose();
    else if (cmd.includes("stop")) stopSession();
    else if (cmd.includes("start")) speakMufasa("Beginning your session.");
    else if (cmd.includes("exit")) exitFullscreen();
  }

  function nextPose() {
    const i = poses.findIndex(p => p.id === activePose.id);
    const next = poses[(i + 1) % poses.length];
    setActivePose(next);
    speakMufasa(`Next pose: ${next.name}.`);
  }

  function stopSession() {
    speakMufasa("Ending session. Great work today!");
    setStatus("Session ended.");
  }

  function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) elem.requestFullscreen();
  }

  function exitFullscreen() {
    if (document.exitFullscreen) document.exitFullscreen();
  }

  return (
    <div className="fit-page">
      <div className="fit-topbar">
        <h1>Mufasa • AI Yoga Coach</h1>
        <p>{status}</p>
      </div>

      <div className="fit-container">
        <div className="fit-video-wrap">
          <video ref={videoRef} className="fit-video" playsInline muted></video>
          <canvas ref={canvasRef} className="fit-canvas"></canvas>

          <div className="fit-overlay">
            <h2>{activePose ? activePose.name : "Loading Pose..."}</h2>
            <p>Score: {poseScore.toFixed(1)}%</p>
            <button onClick={enterFullscreen}>🧘 Fullscreen Mode</button>
          </div>
        </div>

        <div className="fit-side">
          <div className="fit-pose-select">
            <h3>Yoga Poses</h3>
            {poses.map(p => (
              <button
                key={p.id}
                className={p.id === activePose?.id ? "active" : ""}
                onClick={() => setActivePose(p)}
              >
                {p.name}
              </button>
            ))}
          </div>

          {activePose && (
            <div className="fit-pose-info">
              <img src={`/yoga/poses/${activePose.image}`} alt={activePose.name} />
              <p>{activePose.name}</p>
              <div className="fit-score-bar">
                <div
                  className="fit-score-fill"
                  style={{ width: `${poseScore}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
