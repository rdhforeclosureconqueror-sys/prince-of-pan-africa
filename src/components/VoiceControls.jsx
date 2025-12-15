import React, { useState } from "react";
import axios from "axios";
import { FaMicrophone, FaVolumeUp } from "react-icons/fa";

const OPENVOICE_API = "https://ffmpeg-9xhs.onrender.com";

export default function VoiceControls({ text }) {
  const [playing, setPlaying] = useState(false);

  const handleSpeak = async () => {
    try {
      const res = await axios.post(`${OPENVOICE_API}/tts`, { text });
      const audio = new Audio(res.data.audio_url);
      setPlaying(true);
      audio.play();
      audio.onended = () => setPlaying(false);
    } catch {
      alert("Speech playback failed.");
    }
  };

  return (
    <div className="flex gap-4 mt-4">
      <button
        className="bg-pangreen px-4 py-2 rounded flex items-center gap-2"
        onClick={handleSpeak}
        disabled={playing}
      >
        <FaVolumeUp /> {playing ? "Playing..." : "Read Aloud"}
      </button>

      <button
        className="bg-panred px-4 py-2 rounded flex items-center gap-2"
        onClick={() => alert("Voice input coming soon")}
      >
        <FaMicrophone /> Speak
      </button>
    </div>
  );
}
