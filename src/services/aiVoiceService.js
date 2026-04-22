const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function requestAiVoice(text, voiceModel = "alloy") {
  const res = await fetch(`${API_BASE}/chat/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice_model: voiceModel }),
    credentials: "include",
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`AI voice request failed (${res.status}): ${detail}`);
  }

  return res.json();
}

export async function playAiVoice(text, voiceModel = "alloy") {
  const data = await requestAiVoice(text, voiceModel);
  const audioUrl = data.audio_url || data.audioUrl;
  if (!audioUrl) throw new Error("No audio URL returned by AI voice API.");
  const absolute = audioUrl.startsWith("http") ? audioUrl : `${API_BASE}${audioUrl}`;
  const audio = new Audio(absolute);
  await audio.play();
}
