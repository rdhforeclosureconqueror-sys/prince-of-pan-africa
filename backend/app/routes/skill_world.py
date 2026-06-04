from pathlib import Path
import hashlib
import time

from fastapi import APIRouter, HTTPException, Request

from app.routes.chat import (
    normalize_tts_text,
    request_aivoice_tts,
)

router = APIRouter()

GENERATED_SKILL_WORLD_AUDIO_DIR = Path(__file__).resolve().parents[1] / "generated-audio" / "skill-world"
GENERATED_SKILL_WORLD_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_FORMATS = {"mp3", "m4a", "wav"}


def _sanitize_audio_format(format_value: str | None) -> str:
    requested = (format_value or "mp3").strip().lower().lstrip(".")
    return requested if requested in _ALLOWED_FORMATS else "mp3"


def _cache_audio_filename(
    *,
    text: str,
    voice: str,
    audio_format: str,
    speed: float | None,
    pitch: float | None,
    cache_key: str | None,
) -> Path:
    explicit_key = " ".join((cache_key or "").split())
    if explicit_key:
        key_material = f"explicit|{explicit_key}|{voice}|{audio_format}|{speed}|{pitch}"
    else:
        key_material = f"text|{normalize_tts_text(text)}|{voice}|{audio_format}|{speed}|{pitch}"
    digest = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    return GENERATED_SKILL_WORLD_AUDIO_DIR / f"{digest}.{audio_format}"


def _generated_skill_world_audio_url(audio_file: Path) -> str:
    # Garvey-style contract: return a browser-fetchable URL under /generated-audio/skill-world/.
    return f"/generated-audio/skill-world/{audio_file.name}"


@router.post("/api/skill-world/audio")
async def generate_skill_world_audio(payload: dict, request: Request):
    text = normalize_tts_text(payload.get("text", ""))
    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    voice = payload.get("voice") or payload.get("voice_model") or "alloy"
    requested_format = _sanitize_audio_format(payload.get("format"))
    speed = payload.get("speed")
    pitch = payload.get("pitch")
    cache_key = payload.get("cache_key")

    cached_file = _cache_audio_filename(
        text=text,
        voice=voice,
        audio_format=requested_format,
        speed=speed,
        pitch=pitch,
        cache_key=cache_key,
    )
    cached = cached_file.exists()
    started = time.perf_counter()

    if not cached:
        audio_bytes = request_aivoice_tts(
            text=text,
            voice=voice,
            format=requested_format,
            speed=speed,
            pitch=pitch,
        )
        cached_file.write_bytes(audio_bytes)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "audio_url": _generated_skill_world_audio_url(cached_file),
        "cached": cached,
        "voice": voice,
        "format": requested_format,
        "latency_ms": elapsed_ms,
    }
