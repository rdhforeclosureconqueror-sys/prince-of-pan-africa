// ✅ src/utils/mufasaVoice.js
export const MUFASA_TTS_URL = `${import.meta.env.VITE_MUFASA_BRAIN_URL || "https://mufasabrain.onrender.com"}/chat/tts`;

export async function speakMufasa(text, voice_model = "alloy") {
  if (!text?.trim()) return;

  try {
    const res = await fetch(MUFASA_TTS_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice_model }),
    });

    const data = await res.json();
    const audioUrl = data.audio_url || data.audioUrl;
    const audio = new Audio(audioUrl);
    await audio.play();
    return true;
  } catch (err) {
    console.error("Mufasa TTS error:", err);
    // fallback to browser voice
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 0.95;
      u.pitch = 1.0;
      speechSynthesis.speak(u);
    } catch (e) {
      console.warn("Speech fallback failed");
    }
  }
}
