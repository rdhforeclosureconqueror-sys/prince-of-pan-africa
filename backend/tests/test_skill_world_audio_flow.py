from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.routes import skill_world


class AudioResponse:
    status_code = 200
    content = b"ID3 playable mp3 bytes"
    headers = {"content-type": "audio/mpeg"}
    text = "audio bytes"

    def json(self):  # pragma: no cover - raw audio should not be parsed as JSON
        raise AssertionError("TTS upstream audio responses must be handled as raw bytes")


def make_client(tmp_path):
    app = FastAPI()
    app.include_router(skill_world.router)
    app.mount(
        "/generated-audio/skill-world",
        StaticFiles(directory=tmp_path),
        name="generated-skill-world-audio-test",
    )
    return TestClient(app)


def test_skill_world_audio_posts_contract_payload_to_speak_and_returns_audio_url(monkeypatch, tmp_path):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return AudioResponse()

    monkeypatch.setattr(skill_world, "GENERATED_SKILL_WORLD_AUDIO_DIR", tmp_path)
    from app.routes import chat

    monkeypatch.setattr(chat, "SKILL_WORLD_TTS_URL", "https://aivoice-wmrv.onrender.com/tts")
    monkeypatch.setattr(chat.requests, "post", fake_post)
    monkeypatch.setattr(skill_world, "request_aivoice_tts", chat.request_aivoice_tts)

    response = make_client(tmp_path).post(
        "/api/skill-world/audio",
        json={
            "cache_key": "lesson-1",
            "text": " Testing audio ",
            "voice": "alloy",
            "format": "mp3",
            "speed": 1.1,
            "pitch": 0.2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["audio_url"].startswith("/generated-audio/skill-world/")
    assert data["audio_url"].endswith(".mp3")
    assert data["cached"] is False
    assert data["voice"] == "alloy"
    assert data["format"] == "mp3"
    generated_files = list(tmp_path.glob("*.mp3"))
    assert len(generated_files) == 1
    assert generated_files[0].read_bytes() == AudioResponse.content
    assert calls == [
        {
            "url": "https://aivoice-wmrv.onrender.com/speak",
            "json": {
                "text": "Testing audio",
                "voice": "alloy",
                "format": "mp3",
                "speed": 1.1,
                "pitch": 0.2,
            },
            "headers": {"Content-Type": "application/json"},
            "timeout": 45,
            "stream": True,
        }
    ]


def test_skill_world_audio_uses_file_cache_without_second_upstream_call(monkeypatch, tmp_path):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return b"ID3 cached once"

    monkeypatch.setattr(skill_world, "GENERATED_SKILL_WORLD_AUDIO_DIR", tmp_path)
    monkeypatch.setattr(skill_world, "request_aivoice_tts", fake_request)

    client = make_client(tmp_path)
    payload = {"cache_key": "same-lesson", "text": "Testing cache", "voice": "alloy", "format": "mp3"}

    first = client.post("/api/skill-world/audio", json=payload)
    second = client.post("/api/skill-world/audio", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["audio_url"] == second.json()["audio_url"]
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert len(calls) == 1
    assert list(tmp_path.glob("*.mp3"))[0].read_bytes() == b"ID3 cached once"


def test_generated_audio_route_serves_playable_audio_with_content_type(monkeypatch, tmp_path):
    def fake_request(**kwargs):
        return b"RIFF....WAVEfmt playable wav bytes"

    monkeypatch.setattr(skill_world, "GENERATED_SKILL_WORLD_AUDIO_DIR", tmp_path)
    monkeypatch.setattr(skill_world, "request_aivoice_tts", fake_request)

    client = make_client(tmp_path)
    create_response = client.post(
        "/api/skill-world/audio",
        json={"text": "Testing wav", "voice": "alloy", "format": "wav"},
    )
    assert create_response.status_code == 200
    audio_response = client.get(create_response.json()["audio_url"])

    assert audio_response.status_code == 200
    assert audio_response.content == b"RIFF....WAVEfmt playable wav bytes"
    assert audio_response.headers["content-type"].startswith("audio/")


def test_skill_world_audio_rejects_empty_text_before_upstream_call(monkeypatch, tmp_path):
    def fake_request(**kwargs):
        raise AssertionError("empty text must not call upstream")

    monkeypatch.setattr(skill_world, "GENERATED_SKILL_WORLD_AUDIO_DIR", tmp_path)
    monkeypatch.setattr(skill_world, "request_aivoice_tts", fake_request)

    response = make_client(tmp_path).post("/api/skill-world/audio", json={"text": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "No text provided for TTS."
