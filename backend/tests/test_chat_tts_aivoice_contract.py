from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import chat


class AudioResponse:
    status_code = 200
    content = b"ID3 fake mp3 bytes"
    headers = {"content-type": "audio/mpeg"}
    text = "audio bytes"

    def json(self):  # pragma: no cover - successful audio must stay raw bytes
        raise AssertionError("Successful TTS audio responses must not be parsed as JSON")


class MissingInternalTokenResponse:
    status_code = 401
    content = b'{"error":"missing_internal_token"}'
    headers = {"content-type": "application/json"}
    text = '{"error":"missing_internal_token"}'


def make_client():
    app = FastAPI()
    app.include_router(chat.router, prefix="/chat")
    return TestClient(app)


def test_chat_tts_posts_json_to_public_speak_without_auth_header(monkeypatch, tmp_path):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return AudioResponse()

    monkeypatch.setattr(chat, "SKILL_WORLD_TTS_URL", "https://aivoice-wmrv.onrender.com/speak")
    monkeypatch.setattr(chat, "STATIC_AUDIO_DIR", tmp_path)
    monkeypatch.setattr(chat.requests, "post", fake_post)

    response = make_client().post("/chat/tts", json={"text": " Testing audio ", "voice": "alloy"})

    assert response.status_code == 200
    assert response.json()["audio_url"].endswith(".mp3")
    assert calls == [
        {
            "url": "https://aivoice-wmrv.onrender.com/speak",
            "json": {"text": "Testing audio", "voice": "alloy", "format": "mp3"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 45,
            "stream": True,
        }
    ]


def test_chat_request_aivoice_tts_accepts_optional_contract_fields(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return AudioResponse()

    monkeypatch.setattr(chat, "SKILL_WORLD_TTS_URL", "https://aivoice-wmrv.onrender.com/tts")
    monkeypatch.setattr(chat.requests, "post", fake_post)

    audio = chat.request_aivoice_tts(
        text=" Testing options ",
        voice="alloy",
        format="wav",
        speed=1.1,
        pitch=0.2,
    )

    assert audio == AudioResponse.content
    assert calls[0]["url"] == "https://aivoice-wmrv.onrender.com/speak"
    assert calls[0]["json"] == {
        "text": "Testing options",
        "voice": "alloy",
        "format": "wav",
        "speed": 1.1,
        "pitch": 0.2,
    }
    assert "x-internal-token" not in {key.lower() for key in calls[0]["headers"]}
    assert "authorization" not in {key.lower() for key in calls[0]["headers"]}


def test_chat_reports_missing_internal_token_contract_mismatch(monkeypatch):
    def fake_post(url, **kwargs):
        return MissingInternalTokenResponse()

    monkeypatch.setattr(chat, "SKILL_WORLD_TTS_URL", "https://aivoice-wmrv.onrender.com/speak")
    monkeypatch.setattr(chat.requests, "post", fake_post)

    response = make_client().post("/chat/tts", json={"text": "Testing mismatch"})

    assert response.status_code == 401
    detail = response.json()["detail"]
    assert detail["provider_url"] == "https://aivoice-wmrv.onrender.com/speak"
    assert detail["auth_header_sent"] is False
    assert "does not match the repo truth report" in detail["reason"]
