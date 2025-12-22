import React, { useState, useRef, useEffect } from "react";
import { FaMicrophone, FaPlay, FaPause, FaStop } from "react-icons/fa";

export default function VoiceControls({ latestMessage, onVoiceSend }) {
  const [voice, setVoice] = useState("alloy");
  const [audioUrl, setAudioUrl] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [recording, setRecording] = useState(false);
  const [audioTime, setAudioTime] = useState({ current: 0, total: 0 });

  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // ✅ NEW: keep a handle to the mic stream so we can stop it
  const streamRef = useRef(null);

  const baseURL = "https://mufasa-knowledge-bank.onrender.com";

  // ✅ Helper: safely play audio (handles iOS autoplay restrictions)
  const safePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    try {
      await audio.play();
      setPlaying(true);
    } catch (e) {
      // Autoplay can fail until user taps play
      console.warn("Audio play blocked by browser:", e);
      setPlaying(false);
    }
  };

  // ✅ Helper: stop TTS playback cleanly
  const stopAudio = () => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setPlaying(false);
  };

  // ✅ Helper: stop mic tracks (critical)
  const stopMicStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  };

  // 🎧 Play / Pause
  const handlePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      await safePlay();
    }
  };

  // ⏹️ Stop playback
  const handleStop = () => {
    stopAudio();
  };

  // ⏱️ Track playback progress
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setAudioTime({
        current: audio.currentTime,
        total: audio.duration || 0,
      });
    };

    const onEnded = () => setPlaying(false);

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("ended", onEnded);
    };
  }, [audioUrl]);

  // 🗣️ Convert latest message into speech
  const handleGenerateVoice = async () => {
    if (!latestMessage?.trim()) {
      alert("There’s no message to speak yet.");
      return;
    }

    // ✅ Prevent overlap: if recording, stop it first
    if (recording && mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      setRecording(false);
      stopMicStream();
    }

    try {
      const res = await fetch(`${baseURL}/chat/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: latestMessage,
          voice_model: voice,
        }),
      });

      const data = await res.json();
      if (data.audio_url) {
        const fullUrl = data.audio_url.startsWith("http")
          ? data.audio_url
          : `${baseURL}${data.audio_url}`;

        setAudioUrl(fullUrl);

        // ✅ Stop any existing playback first
        stopAudio();

        // ✅ Play as soon as the element updates
        setTimeout(() => {
          safePlay();
        }, 150);
      } else {
        alert("Mufasa could not generate voice.");
      }
    } catch (err) {
      console.error("TTS Error:", err);
      alert("There was a problem generating Mufasa’s voice.");
    }
  };

  // 🎙️ Record and send voice input
  const handleRecord = async () => {
    // If currently recording, stop
    if (recording) {
      if (mediaRecorderRef.current?.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setRecording(false);
      // stream will be stopped in onstop as well, but do it here too (safe)
      stopMicStream();
      return;
    }

    // ✅ Prevent overlap: stop TTS audio before opening mic
    stopAudio();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // ✅ CRITICAL: release the mic hardware
        stopMicStream();

        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });

        if (onVoiceSend) {
          onVoiceSend(audioBlob);
        } else {
          console.warn("⚠️ onVoiceSend not connected to parent component.");
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      console.error("Mic access denied:", err);
      alert("Please allow microphone access to speak with Mufasa.");
    }
  };

  // ✅ Cleanup on unmount (prevents lingering mic lock)
  useEffect(() => {
    return () => {
      try {
        if (mediaRecorderRef.current?.state === "recording") {
          mediaRecorderRef.current.stop();
        }
      } catch {}
      stopMicStream();
      stopAudio();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatTime = (time) => {
    const m = Math.floor(time / 60).toString().padStart(2, "0");
    const s = Math.floor(time % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="p-4 bg-black/50 rounded-2xl border border-yellow-600 shadow-md text-center mt-4">
      <h2 className="text-xl font-bold mb-3 text-yellow-400">🦁 Mufasa Voice</h2>

      <div className="flex items-center justify-center gap-2 mb-3">
        <label htmlFor="voice" className="text-yellow-300 text-sm">
          Voice:
        </label>
        <select
          id="voice"
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
          className="bg-black text-yellow-300 border border-yellow-600 rounded px-2 py-1"
        >
          <option value="alloy">Alloy (Strong)</option>
          <option value="verse">Verse (Smooth)</option>
          <option value="echo">Echo (Narrative)</option>
        </select>
      </div>

      <div className="flex justify-center flex-wrap gap-3">
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
