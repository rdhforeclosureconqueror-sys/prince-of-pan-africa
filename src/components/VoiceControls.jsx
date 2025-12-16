import React, { useState } from "react";
import axios from "axios";
import { FaMicrophone, FaVolumeUp, FaStop } from "react-icons/fa";

const MUFASA_API = import.meta.env.VITE_MUFASA_API || "https://mufasa-knowledge-bank.onrender.com";

export default function VoiceControls({ latestMessage }) {
  const [voice, setVoice] = useState("alloy");
  const [recording, setRecording] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePlayVoice = async () => {
    if (!latestMessage) {
      alert("No recent reply to play.");
      return;
    }
    try {
      setLoading(true);
      const res = await axios.post(`${MUFASA_API}/chat/message`, {
        message: latestMessage,
        voice: true,
      });
      const audioUrl = res.data.audio_url;
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        setPlaying(true);
        audio.play();
        audio.onended = () => setPlaying(false);
      } else {
        alert("No voice available for this message.");
      }
    } catch (error) {
      console.error("Voice playback failed:", error);
      alert("Voice playback failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRecord = async () => {
    alert("🎤 Voice input feature coming soon!");
  };

  return (
    <div className="p-4 bg-black/40 rounded-lg border border-yellow-700 shadow-md mt-4">
      <h2 className="text-xl font-bold mb-2 text-yellow-400 flex items-center gap-2">
        🦁 Mufasa Voice Controls
      </h2>

      {/* Voice selection dropdown */}
      <div className="flex items-center gap-2 mb-3">
        <label htmlFor="voice" className="text-yellow-200 text-sm">
          Choose Voice:
        </label>
        <select
          id="voice"
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
          className="bg-black text-yellow-300 border border-yellow-700 rounded px-2 py-1"
        >
          <option value="alloy">Alloy (Strong & Deep)</option>
          <option value="verse">Verse (Smooth & Warm)</option>
          <option value="echo">Echo (Narrative)</option>
        </select>
      </div>

      {/* Buttons */}
      <div className="flex gap-3 justify-center">
        <button
          onClick={handlePlayVoice}
          disabled={loading || playing}
          className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded flex items-center gap-2 font-semibold"
        >
          <FaVolumeUp />
          {playing ? "Playing..." : loading ? "Loading Voice..." : "Play Voice"}
        </button>

        <button
          onClick={handleRecord}
          className={`${
            recording ? "bg-red-600" : "bg-green-600 hover:bg-green-500"
          } text-black px-4 py-2 rounded flex items-center gap-2 font-semibold`}
        >
          {recording ? <FaStop /> : <FaMicrophone />}
          {recording ? "Stop" : "Speak"}
        </button>
      </div>
    </div>
  );
}
