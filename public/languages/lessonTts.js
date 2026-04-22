(function () {
  const memoryCache = new Map();
  let activeController = null;

  function stopPlayer(player) {
    if (!player) return;
    try {
      player.pause();
      player.currentTime = 0;
    } catch (e) {
      // ignore
    }
  }

  function cacheKey(text, voice) {
    return `${voice || "alloy"}::${(text || "").trim()}`;
  }

  function getCachedAudioUrl(text, voice) {
    const key = cacheKey(text, voice);
    if (memoryCache.has(key)) return memoryCache.get(key);
    return null;
  }

  function setCachedAudioUrl(text, voice, url) {
    if (!url) return;
    memoryCache.set(cacheKey(text, voice), url);
  }

  async function speakWithBackend({ text, voice = "alloy", endpoint = "", player, onStatus, signal }) {
    if (onStatus) onStatus("Dispatching voice request…");

    const startedAt = performance.now();
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ text, voice_model: voice }),
      signal,
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

    setCachedAudioUrl(text, voice, data.audio_url);
    player.src = data.audio_url;
    await player.play();

    if (onStatus) {
      const totalMs = Math.round(performance.now() - startedAt);
      const cacheHit = data.cached ? "cache hit" : "fresh render";
      onStatus(`AI voice playing • ${cacheHit} • ${totalMs}ms`);
    }
  }

  async function prefetch({ text, voice, endpoint, onStatus }) {
    if (!text || !text.trim()) return null;
    const cachedUrl = getCachedAudioUrl(text, voice);
    if (cachedUrl) return cachedUrl;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ text, voice_model: voice || "alloy" }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.audio_url) {
      setCachedAudioUrl(text, voice, data.audio_url);
      if (onStatus) onStatus("Prefetched next lesson audio.");
      return data.audio_url;
    }
    return null;
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

    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();

    const cachedUrl = getCachedAudioUrl(text, voice);
    if (cachedUrl) {
      player.src = cachedUrl;
      await player.play();
      if (onStatus) onStatus("AI voice playing • local cache hit");
      return;
    }

    try {
      await speakWithBackend({
        text,
        voice,
        endpoint,
        player,
        onStatus,
        signal: activeController.signal,
      });
    } catch (error) {
      if (error?.name === "AbortError") {
        if (onStatus) onStatus("Previous voice request canceled.");
        return;
      }
      browserFallback(text, onStatus);
      throw error;
    }
  }

  window.lessonTts = { speak, stopPlayer, prefetch };
})();
