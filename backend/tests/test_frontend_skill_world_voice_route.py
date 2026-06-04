from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_voice_controls_uses_shared_skill_world_audio_route_and_payload_shape():
    source = (REPO_ROOT / "src" / "components" / "VoiceControls.jsx").read_text()

    assert 'fetch(`${baseURL}/api/skill-world/audio`, {' in source
    assert '/chat/tts' not in source
    assert 'text: latestMessage' in source
    assert 'voice_model: voice' in source
    assert 'data.audio_url' in source
    assert 'data.cached' in source
