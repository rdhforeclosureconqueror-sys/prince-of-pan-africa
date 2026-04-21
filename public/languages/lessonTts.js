(function () {
  function stopPlayer(player) {
    if (!player) return;
    try {
      player.pause();
      player.currentTime = 0;
    } catch (e) {
      // ignore
    }
  }

  async function speakWithBackend({ text, voice = "alloy", endpoint = "", player, onStatus }) {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ text, voice_model: voice }),
    });

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const data = await res.json();
        detail = data.detail || detail;
      } catch (_) {
        // non-json response
      }
      throw new Error(detail);
    }

    const data = await res.json();
    if (!data?.audio_url) {
      throw new Error("Missing audio_url in TTS response");
    }

    player.src = data.audio_url;
    await player.play();
    if (onStatus) onStatus("AI voice playing.");
  }

  function browserFallback(text, onStatus) {
    if (!window.speechSynthesis || !text) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
      if (onStatus) onStatus("Voice playing.");
    } catch (e) {
      if (onStatus) onStatus("Voice unavailable on this browser.");
    }
  }

  async function speak({ text, voice, endpoint, playerId = "aiTtsPlayer", onStatus }) {
    if (!text || !text.trim()) return;
    const player = document.getElementById(playerId);
    if (!player) throw new Error("Audio player not found");

    stopPlayer(player);

    try {
      await speakWithBackend({ text, voice, endpoint, player, onStatus });
    } catch (error) {
      browserFallback(text, onStatus);
      throw error;
    }
  }

  window.lessonTts = { speak, stopPlayer };
})();
