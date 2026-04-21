// src/api/mufasaClient.js

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Generic helper for calling the Mufasa Knowledge Bank API
 */
async function callMufasaAPI(endpoint, payload = {}, method = "POST") {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body: method === "POST" ? JSON.stringify(payload) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mufasa API Error ${res.status}: ${text}`);
    }

    return await res.json();
  } catch (error) {
    console.error("❌ Mufasa API Request Failed:", error);
    return { error: error.message };
  }
}

/**
 * 🧠 Send a message to Mufasa (text chat, optionally with voice)
 * @param {string} message - The user’s input message
 * @param {boolean} voice - Whether to also generate TTS audio
 * @param {string} voiceModel - Which voice to use ("alloy", "verse", "echo")
 */
export async function sendChatMessage(message, voice = false, voiceModel = "alloy") {
  if (!message?.trim()) {
    return { reply: "⚠️ Empty message.", audio_url: null };
  }

  try {
    const data = await callMufasaAPI("/chat/message", {
      message,
      voice,
      voice_model: voiceModel,
    });

    return {
      reply:
        data.reply ||
        data.response ||
        data.answer ||
        "🦁 Mufasa is silent...",
      audio_url: data.audio_url || null,
      voice: data.voice || voiceModel,
    };
  } catch (error) {
    console.error("❌ sendChatMessage Error:", error);
    return {
      reply: "⚠️ Could not reach Mufasa. Check your backend connection.",
      audio_url: null,
    };
  }
}

/**
 * 🎧 Generate TTS from an existing text reply (faster + consistent)
 * @param {string} text - Text to convert into speech
 * @param {string} voiceModel - The selected voice model
 */
export async function generateTTS(text, voiceModel = "alloy") {
  if (!text?.trim()) return { error: "No text provided." };

  try {
    const data = await callMufasaAPI("/chat/tts", {
      text,
      voice_model: voiceModel,
    });
    return data; // { audio_url, voice }
  } catch (error) {
    console.error("❌ generateTTS Error:", error);
    return { error: error.message };
  }
}

/**
 * 🎙️ Send recorded voice input to Mufasa for STT + GPT reply + TTS
 * @param {File} audioFile - Recorded voice blob (webm)
 */
export async function sendVoiceMessage(audioFile) {
  try {
    const formData = new FormData();
    formData.append("file", audioFile, "voice.webm");

    const res = await fetch(`${API_BASE}/chat/voice`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Voice chat error ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error("🎤 Voice message failed:", error);
    return { error: error.message };
  }
}

/**
 * 🌍 Health check
 */
export async function checkHealth() {
  return callMufasaAPI("/health", {}, "GET");
}

/**
 * 🧩 Get API Info
 */
export async function getAPIInfo() {
  return callMufasaAPI("/info", {}, "GET");
}
