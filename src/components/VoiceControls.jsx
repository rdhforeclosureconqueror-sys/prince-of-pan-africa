import React, { useState, useRef } from "react";
import axios from "axios";
import { FaMicrophone, FaVolumeUp, FaStop } from "react-icons/fa";

const MUFASA_API = import.meta.env.VITE_MUFASA_API || "https://mufasa-knowledge-bank.onrender.com";

export default function VoiceControls({ latestMessage }) {
  const [voice, setVoice] = useState("alloy");
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [replyAudioUrl, setReplyAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 🔊 Generate and play voice from latest message (if any)
  const handlePlayVoice = async () => {
    if (!latestMessage || latestMessage.trim().length === 0) {
      alert("No recent message to play.");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${MUFASA_API}/chat/message`, {
        message: latestMessage,
        voice: true,
        voice_model: voice,
      });

      const audioUrl = res.data.audio_url;
      setReplyAudioUrl(audioUrl);

      if (audioUrl) {
        const audio = new Audio(audioUrl);
        setPlaying(true);
        audio.play();
        audio.onended = () => setPlaying(false);
      } else {
        alert("No voice generated.");
      }
    } catch (err) {
      console.error("Voice playback failed:", err);
      alert("⚠️ Could not play voice.");
    } finally {
      setLoading(false);
    }
  };

  // 🎙️ Record user voice → Send to /chat/voice → Get reply
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
          setLoading(true);
          const res = await axios.post(`${MUFASA_API}/chat/voice`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });

          console.log("🦁 Voice chat result:", res.data);
          const reply = res.data.reply;
          const audioUrl = res.data.audio_url;

          if (audioUrl) {
            setReplyAudioUrl(audioUrl);
            const audio = new Audio(audioUrl);
            setPlaying(true);
            audio.play();
            audio.onended = () => setPlaying(false);
          } else {
            alert("No voice generated for this reply.");
          }
        } catch (err) {
          console.error("Voice chat failed:", err);
          alert("❌ Voice chat failed.");
        } finally {
          setLoading(false);
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      console.error("Mic access denied:", err);
      alert("🎤 Please allow microphone access.");
    }
  };

  return (
    <div className="p-4 bg-black/40 rounded-lg border border-yellow-700 shadow-md text-center mt-4">
      <h2 className="text-xl font-bold mb-3 text-yellow-400">
        🦁 Mufasa Voice Controls
      </h2>

      {/* Voice selector */}
      <div className="flex items-center justify-center gap-2 mb-3">
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
      <div className="flex justify-center gap-4">
        <button
          onClick={handlePlayVoice}
          disabled={playing || loading}
          className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded flex items-center gap-2 font-semibold"
        >
          <FaVolumeUp />
          {playing
            ? "Playing..."
            : loading
            ? "Loading..."
            : "Play Mufasa’s Voice"}
        </button>

        <button
          onClick={handleRecord}
          className={`${
            recording ? "bg-red-600 hover:bg-red-500" : "bg-green-600 hover:bg-green-500"
          } text-black px-4 py-2 rounded flex items-center gap-2 font-semibold`}
        >
          {recording ? <FaStop /> : <FaMicrophone />}
          {recording ? "Stop Recording" : "Speak"}
        </button>
      </div>

      {/* Optional: show if a voice reply is ready */}
      {replyAudioUrl && !playing && (
        <div className="mt-3 text-sm text-yellow-300">
          ✅ Voice reply ready. Click “Play Mufasa’s Voice” to hear it again.
        </div>
      )}
    </div>
  );
}
