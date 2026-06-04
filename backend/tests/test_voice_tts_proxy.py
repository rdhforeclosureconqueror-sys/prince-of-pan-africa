from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import voice


class AudioResponse:
    status_code = 200
    content = b"ID3 fake mp3 bytes"
    headers = {"content-type": "audio/mpeg"}
    text = "audio bytes"

    def json(self):  # pragma: no cover - this must never be reached for audio responses
        raise AssertionError("Successful TTS audio responses must not be parsed as JSON")


class WavAudioResponse(AudioResponse):
    content = b"RIFF fake wav bytes"
    headers = {"content-type": "audio/wav"}


class ErrorResponse:
    status_code = 405
    content = b'{"detail":"Method Not Allowed"}'
    headers = {"content-type": "application/json"}
    text = '{"detail":"Method Not Allowed"}'


def make_client():
    app = FastAPI()
    app.include_router(voice.router, prefix="/api/voice")
    return TestClient(app)


def test_tts_proxy_normalizes_configured_urls_to_canonical_speak_endpoint(monkeypatch):
    variants = [
        "https://aivoice-wmrv.onrender.com",
        "https://aivoice-wmrv.onrender.com/",
        "https://aivoice-wmrv.onrender.com/tts",
        "https://aivoice-wmrv.onrender.com/speak",
    ]

    for configured_url in variants:
        monkeypatch.setattr(voice, "AIVOICE_BASE_URL", configured_url)

        assert voice._aivoice_speak_url() == "https://aivoice-wmrv.onrender.com/speak"


def test_tts_proxy_posts_json_to_canonical_speak_endpoint(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return AudioResponse()

    monkeypatch.setattr(voice, "AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com/tts")
    monkeypatch.setattr(voice.requests, "post", fake_post)

    response = make_client().post(
        "/api/voice/tts",
        json={"text": " Testing 1 2 3 ", "voice": "alloy", "format": "mp3", "speed": 1.1, "pitch": 0.2},
    )

    assert response.status_code == 200
    assert calls == [
        {
            "url": "https://aivoice-wmrv.onrender.com/speak",
            "json": {"text": "Testing 1 2 3", "voice": "alloy", "format": "mp3", "speed": 1.1, "pitch": 0.2},
            "headers": {"Content-Type": "application/json"},
            "timeout": 60,
        }
    ]


def test_tts_proxy_forwards_raw_audio_and_preserves_content_type(monkeypatch):
    def fake_post(url, **kwargs):
        return WavAudioResponse()

    monkeypatch.setattr(voice.requests, "post", fake_post)

    response = make_client().post("/api/voice/tts", json={"text": "Testing audio"})

    assert response.status_code == 200
    assert response.content == WavAudioResponse.content
    assert response.headers["content-type"] == "audio/wav"


def test_tts_proxy_rejects_empty_text_before_upstream_call(monkeypatch):
    def fake_post(url, **kwargs):
        raise AssertionError("Empty TTS text should not be sent upstream")

    monkeypatch.setattr(voice.requests, "post", fake_post)

    response = make_client().post("/api/voice/tts", json={"text": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "No text provided for TTS."}


def test_tts_proxy_preserves_upstream_error_status_and_message(monkeypatch):
    def fake_post(url, **kwargs):
        return ErrorResponse()

    monkeypatch.setattr(voice.requests, "post", fake_post)

    response = make_client().post("/api/voice/tts", json={"text": "Testing error"})

    assert response.status_code == 405
    assert response.json() == {"detail": ErrorResponse.text}
