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

  const DEFAULT_API_ORIGIN = "https://api.simbawaujamaa.com";
  const DEFAULT_AUDIO_FORMAT = "mp3";
  const DEFAULT_SPEED = 1.0;
  const DEFAULT_PITCH = 0.0;

  function shouldUseProductionApiOrigin() {
    const host = window.location?.hostname || "";
    return host === "simbawaujamaa.com" || host === "www.simbawaujamaa.com";
  }

  function normalizeRequestUrl(endpoint = "") {
    if (/^https?:\/\//i.test(endpoint)) return endpoint;
    const path = endpoint || "/api/skill-world/audio";
    const base = shouldUseProductionApiOrigin() ? DEFAULT_API_ORIGIN : window.location.origin;
    return new URL(path, base).toString();
  }

  function normalizeAudioUrl(audioUrl, requestUrl) {
    if (!audioUrl) return "";
    if (/^https?:\/\//i.test(audioUrl)) return audioUrl;
    const requestOrigin = new URL(requestUrl, window.location.origin).origin;
    return new URL(audioUrl, requestOrigin).toString();
  }

  function safeLog(event, details = {}) {
    try {
      console.log(event, details);
    } catch (_) {
      // logging must never break voice playback
    }
  }

  function buildPayload({ text, voice, format, speed, pitch, cacheKey }) {
    const selectedVoice = voice || "alloy";
    const payload = {
      text: (text || "").trim(),
      voice_model: selectedVoice,
      voice: selectedVoice,
      format: format || DEFAULT_AUDIO_FORMAT,
      speed: speed ?? DEFAULT_SPEED,
      pitch: pitch ?? DEFAULT_PITCH,
    };
    if (cacheKey) payload.cache_key = cacheKey;
    return payload;
  }

  async function speakWithBackend({ text, voice = "alloy", endpoint = "", player, onStatus, signal, language = "unknown", format = DEFAULT_AUDIO_FORMAT, speed = DEFAULT_SPEED, pitch = DEFAULT_PITCH, cacheKey }) {
    const requestUrl = normalizeRequestUrl(endpoint);
    const payload = buildPayload({ text, voice, format, speed, pitch, cacheKey });
    safeLog("static_language_tts_click", {
      language,
      request_url: requestUrl,
      text_present: Boolean(payload.text),
    });
    if (onStatus) onStatus("Dispatching voice request…");

    const startedAt = performance.now();
    const res = await fetch(requestUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
    safeLog("static_language_tts_response", {
      language,
      request_url: requestUrl,
      response_status: res.status,
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
    const normalizedAudioUrl = normalizeAudioUrl(data?.audio_url, requestUrl);
    safeLog("static_language_tts_audio_url", {
      language,
      request_url: requestUrl,
      audio_url_present: Boolean(normalizedAudioUrl),
    });
    if (!normalizedAudioUrl) {
      throw new Error("Missing audio_url in TTS response");
    }

    setCachedAudioUrl(text, voice, normalizedAudioUrl);
    player.src = normalizedAudioUrl;
    await player.play();
    safeLog("static_language_tts_play", {
      language,
      request_url: requestUrl,
      audio_url_present: true,
      play_started: true,
    });

    if (onStatus) {
      const totalMs = Math.round(performance.now() - startedAt);
      const cacheHit = data.cached ? "cache hit" : "fresh render";
      onStatus(`AI voice playing • ${cacheHit} • ${totalMs}ms`);
    }
  }

  async function prefetch({ text, voice, endpoint, onStatus, language = "unknown", format = DEFAULT_AUDIO_FORMAT, speed = DEFAULT_SPEED, pitch = DEFAULT_PITCH, cacheKey }) {
    if (!text || !text.trim()) return null;
    const cachedUrl = getCachedAudioUrl(text, voice);
    if (cachedUrl) return cachedUrl;

    const requestUrl = normalizeRequestUrl(endpoint);
    const res = await fetch(requestUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(buildPayload({ text, voice, format, speed, pitch, cacheKey })),
    });
    if (!res.ok) return null;
    const data = await res.json();
    const normalizedAudioUrl = normalizeAudioUrl(data?.audio_url, requestUrl);
    if (normalizedAudioUrl) {
      setCachedAudioUrl(text, voice, normalizedAudioUrl);
      if (onStatus) onStatus("Prefetched next lesson audio.");
      return normalizedAudioUrl;
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

  async function speak({ text, voice, endpoint, playerId = "aiTtsPlayer", onStatus, language = "unknown", format = DEFAULT_AUDIO_FORMAT, speed = DEFAULT_SPEED, pitch = DEFAULT_PITCH, cacheKey }) {
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
        language,
        format,
        speed,
        pitch,
        cacheKey,
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
