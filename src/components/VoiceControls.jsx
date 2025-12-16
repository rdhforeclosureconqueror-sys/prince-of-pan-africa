import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FaMicrophone, FaPlay, FaPause, FaStop } from "react-icons/fa";

const MUFASA_API =
  import.meta.env.VITE_MUFASA_API || "https://mufasa-knowledge-bank.onrender.com";

export default function VoiceControls({ latestMessage }) {
  const [voice, setVoice] = useState("alloy");
  const [audioUrl, setAudioUrl] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [recording, setRecording] = useState(false);
  const [audioTime, setAudioTime] = useState({ current: 0, total: 0 });
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 🎧 Generate audio from existing text
  const handleGenerateVoice = async () => {
    if (!latestMessage?.trim()) {
      alert("There’s no message to speak yet.");
      return;
    }

    try {
      const res = await axios.post(`${MUFASA_API}/chat/tts`, {
        text: latestMessage,
        voice_model: voice,
      });
      setAudioUrl(res.data.audio_url);
    } catch (err) {
      console.error("TTS error:", err);
      alert("Failed to generate voice.");
    }
  };

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play();
      setPlaying(true);
    }
  };

  const handleStop = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      setPlaying(false);
    }
  };

  // ⏱️ Update playback time
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setAudioTime({
        current: audio.currentTime,
        total: audio.duration || 0,
      });
    };

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("ended", () => setPlaying(false));

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
    };
  }, [audioUrl]);

  // 🎙️ Record speech and send for chat reply (optional)
  const handleRecord = async () => {
    if (recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");

        try {
          const res = await axios.post(`${MUFASA_API}/chat/voice`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          console.log("Voice chat result:", res.data);
        } catch (err) {
          console.error("Voice chat failed:", err);
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      console.error("Mic access denied:", err);
      alert("Please allow microphone access.");
    }
  };

  // Format timer mm:ss
  const formatTime = (time) => {
    const m = Math.floor(time / 60)
      .toString()
      .padStart(2, "0");
    const s = Math.floor(time % 60)
      .toString()
      .padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="p-4 bg-black/40 rounded-lg border border-yellow-700 shadow-md text-center mt-4">
      <h2 className="text-xl font-bold mb-3 text-yellow-400">🦁 Mufasa Voice</h2>

      <div className="flex items-center justify-center gap-2 mb-3">
        <label htmlFor="voice" className="text-yellow-200 text-sm">
          Voice:
        </label>
        <select
          id="voice"
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
          className="bg-black text-yellow-300 border border-yellow-700 rounded px-2 py-1"
        >
          <option value="alloy">Alloy (Strong)</option>
          <option value="verse">Verse (Smooth)</option>
          <option value="echo">Echo (Narrative)</option>
        </select>
      </div>

      <div className="flex justify-center gap-3">
        <button
          onClick={handleGenerateVoice}
          className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded font-semibold"
        >
          Generate Voice
        </button>

        <button
          onClick={handlePlayPause}
          disabled={!audioUrl}
          className="bg-green-600 hover:bg-green-500 text-black px-4 py-2 rounded font-semibold flex items-center gap-2"
        >
          {playing ? <FaPause /> : <FaPlay />}
          {playing ? "Pause" : "Play"}
        </button>

        <button
          onClick={handleStop}
          disabled={!audioUrl}
          className="bg-red-600 hover:bg-red-500 text-black px-4 py-2 rounded font-semibold flex items-center gap-2"
        >
          <FaStop /> Stop
        </button>

        <button
          onClick={handleRecord}
          className={`${
            recording ? "bg-red-600 hover:bg-red-500" : "bg-blue-600 hover:bg-blue-500"
          } text-black px-4 py-2 rounded font-semibold flex items-center gap-2`}
        >
          <FaMicrophone />
          {recording ? "Stop Recording" : "Speak"}
        </button>
      </div>

      {/* Timer + Player */}
      {audioUrl && (
        <div className="mt-3 text-yellow-300 text-sm">
          {formatTime(audioTime.current)} /{" "}
          {audioTime.total ? formatTime(audioTime.total) : "00:00"}
          <audio ref={audioRef} src={audioUrl} preload="auto" hidden />
        </div>
      )}
    </div>
  );
}
