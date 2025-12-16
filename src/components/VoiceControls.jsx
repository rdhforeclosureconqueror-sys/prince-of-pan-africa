import React, { useState, useRef } from "react";
import axios from "axios";
import { FaMicrophone, FaVolumeUp, FaStop } from "react-icons/fa";

const MUFASA_API = import.meta.env.VITE_MUFASA_API || "https://mufasa-knowledge-bank.onrender.com";

export default function VoiceControls() {
  const [text, setText] = useState("");
  const [reply, setReply] = useState("");
  const [recording, setRecording] = useState(false);
  const [playing, setPlaying] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 🗣️ Send text to Mufasa and play his reply
  const handleSpeak = async () => {
    if (!text.trim()) return alert("Enter a message first!");

    try {
      setReply("");
      const res = await axios.post(`${MUFASA_API}/chat/message`, {
        message: text,
        voice: true,
      });

      setReply(res.data.reply);
      console.log("🦁 Mufasa reply:", res.data);

      if (res.data.audio_url) {
        const audio = new Audio(res.data.audio_url);
        setPlaying(true);
        audio.play();
        audio.onended = () => setPlaying(false);
      }
    } catch (err) {
      console.error("Chat failed:", err);
      alert("⚠️ Could not connect to Mufasa.");
    }
  };

  // 🎙️ Record user voice and send to Mufasa voice chat
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

          console.log("🦁 Voice chat result:", res.data);
          setReply(res.data.reply);

          if (res.data.audio_url) {
            const audio = new Audio(res.data.audio_url);
            setPlaying(true);
            audio.play();
            audio.onended = () => setPlaying(false);
          }
        } catch (err) {
          console.error("Voice chat failed:", err);
          alert("❌ Voice chat failed.");
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
    <div className="p-4 bg-black/30 rounded-lg border border-yellow-700 shadow-md text-center">
      <h2 className="text-xl font-bold mb-3 text-yellow-400">
        🦁 Talk to Mufasa
      </h2>

      {/* Input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask Mufasa something wise..."
        className="w-full p-3 rounded bg-black text-white border border-yellow-600 mb-3 resize-none"
        rows={3}
      />

      {/* Buttons */}
      <div className="flex justify-center gap-4">
        <button
          onClick={handleSpeak}
          disabled={playing}
          className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded flex items-center gap-2 font-semibold"
        >
          <FaVolumeUp />
          {playing ? "Playing..." : "Ask Mufasa"}
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

      {/* Reply */}
      {reply && (
        <div className="mt-4 p-3 bg-black/60 rounded border border-yellow-700 text-yellow-200 text-left whitespace-pre-line">
          {reply}
        </div>
      )}
    </div>
  );
}
