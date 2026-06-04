from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LANGUAGE_DIR = REPO_ROOT / "public" / "languages"


def _read_language_source(language: str) -> str:
    return (LANGUAGE_DIR / f"{language}.html").read_text()


def test_shared_static_language_tts_client_uses_skill_world_contract():
    source = (LANGUAGE_DIR / "lessonTts.js").read_text()

    assert 'const DEFAULT_API_ORIGIN = "https://api.simbawaujamaa.com";' in source
    assert 'const path = endpoint || "/api/skill-world/audio";' in source
    assert 'fetch(requestUrl, {' in source
    assert 'voice_model: selectedVoice' in source
    assert 'voice: selectedVoice' in source
    assert 'format: format || DEFAULT_AUDIO_FORMAT' in source
    assert 'speed: speed ?? DEFAULT_SPEED' in source
    assert 'pitch: pitch ?? DEFAULT_PITCH' in source
    assert 'if (cacheKey) payload.cache_key = cacheKey;' in source
    assert 'normalizeAudioUrl(data?.audio_url, requestUrl)' in source
    assert 'player.src = normalizedAudioUrl' in source
    assert 'await player.play()' in source
    assert 'static_language_tts_click' in source
    assert 'response_status: res.status' in source
    assert 'audio_url_present: Boolean(normalizedAudioUrl)' in source
    assert 'play_started: true' in source
    assert '/chat/tts' not in source
    assert '/api/voice/tts' not in source


def test_swahili_static_language_page_sends_visible_lesson_text_to_skill_world_audio():
    source = _read_language_source("swahili")

    assert 'const TTS_ENDPOINT = "/api/skill-world/audio";' in source
    assert 'const LANGUAGE_CODE = "swahili";' in source
    assert 'function buildVisibleLessonText(d)' in source
    assert 'await speak(buildVisibleLessonText(d), { cacheKey: `${LANGUAGE_CODE}-day-${d.day}-lesson` });' in source
    assert 'window.lessonTts.speak({' in source
    assert 'endpoint: TTS_ENDPOINT' in source
    assert 'language: LANGUAGE_CODE' in source
    assert 'format: "mp3"' in source
    assert 'speed: DEFAULT_TTS_SPEED' in source
    assert 'pitch: DEFAULT_TTS_PITCH' in source
    assert 'cacheKey: options.cacheKey' in source
    assert '/chat/tts' not in source
    assert '/api/voice/tts' not in source


def test_yoruba_static_language_page_sends_visible_lesson_text_to_skill_world_audio():
    source = _read_language_source("yoruba")

    assert 'const TTS_ENDPOINT = "/api/skill-world/audio";' in source
    assert 'const LANGUAGE_CODE = "yoruba";' in source
    assert 'function buildVisibleLessonText(d)' in source
    assert 'await speak(buildVisibleLessonText(d), { cacheKey: `${LANGUAGE_CODE}-day-${d.day}-lesson` });' in source
    assert 'window.lessonTts.speak({' in source
    assert 'endpoint: TTS_ENDPOINT' in source
    assert 'language: LANGUAGE_CODE' in source
    assert 'format: "mp3"' in source
    assert 'speed: DEFAULT_TTS_SPEED' in source
    assert 'pitch: DEFAULT_TTS_PITCH' in source
    assert 'cacheKey: options.cacheKey' in source
    assert '/chat/tts' not in source
    assert '/api/voice/tts' not in source
