import { playAiVoice } from "../services/aiVoiceService";

export async function speakMufasa(text, voice_model = "alloy") {
  if (!text?.trim()) return;

  try {
    await playAiVoice(text, voice_model);
    return true;
  } catch (err) {
    console.error("Mufasa TTS error:", err);
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
