from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from openai import OpenAI
import requests
import tempfile
import os
import uuid
import logging
import hashlib
import time
from pathlib import Path
from app.config import settings

router = APIRouter()

STATIC_AUDIO_DIR = Path(__file__).resolve().parents[1] / "static" / "audio"
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

MUFASA_MODEL = "gpt-4o-mini"
AIVOICE_BASE_URL = settings.AIVOICE_BASE_URL
AIVOICE_API_KEY = settings.AIVOICE_API_KEY
OPENAI_API_KEY = settings.OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY or "DUMMY_KEY")
logger = logging.getLogger("mufasa-chat-voice")


def aivoice_headers():
    headers = {"Content-Type": "application/json"}
    if AIVOICE_API_KEY:
        headers["X-AIVOICE-KEY"] = AIVOICE_API_KEY
    return headers


def _masked_key(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _tts_error_reason(status_code: int | None, body_snippet: str, err: Exception | None = None) -> str:
    lowered = (body_snippet or "").lower()
    if err is not None:
        return "network unreachable"
    if status_code in {401, 403} or "invalid api key" in lowered or "unauthorized" in lowered:
        return "invalid API key"
    if status_code == 404:
        return "incorrect endpoint path"
    if status_code in {400, 415, 422}:
        return "incorrect request body format"
    return "provider rejected request"


def generate_audio_filename(ext="mp3"):
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"


def save_audio_file(audio_bytes, ext="mp3"):
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return filename


def cache_audio_filename(text: str, voice: str, ext: str = "mp3") -> Path:
    digest = hashlib.sha256(f"{voice}|{(text or '').strip()}".encode("utf-8")).hexdigest()
    return STATIC_AUDIO_DIR / f"{digest}.{ext}"


def build_audio_url(request: Request | None, audio_file: Path, base_url: str | None = None) -> str:
    if request is not None:
        return str(request.url_for("static", path=f"audio/{audio_file.name}"))
    if base_url:
        return f"{base_url.rstrip('/')}/static/audio/{audio_file.name}"
    raise HTTPException(status_code=500, detail="Cannot build audio URL without request/base URL context.")




def normalize_tts_text(text: str) -> str:
    normalized = " ".join((text or "").split())
    return normalized.strip()


def generate_tts_audio_url(*, request: Request | None, text: str, voice: str = "alloy", base_url: str | None = None) -> tuple[str, bool]:
    normalized_text = normalize_tts_text(text)
    if not normalized_text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    cached_file = cache_audio_filename(text=normalized_text, voice=voice)
    cached = cached_file.exists()

    if not cached:
        audio_bytes = request_aivoice_tts(text=normalized_text, voice=voice)
        with open(cached_file, "wb") as f:
            f.write(audio_bytes)

    audio_url = build_audio_url(request, cached_file, base_url=base_url)
    return audio_url, cached
def request_aivoice_tts(
    *,
    text: str,
    voice: str | None = None,
    format: str | None = "mp3",
    timeout: int = 45,
):
    payload = {"text": text}
    if voice:
        payload["voice"] = voice
    if format:
        payload["format"] = format
    provider_url = f"{AIVOICE_BASE_URL.rstrip('/')}/speak"
    headers = aivoice_headers()
    logged_headers = dict(headers)
    logged_headers["X-AIVOICE-KEY"] = _masked_key(headers.get("X-AIVOICE-KEY"))

    logger.info(
        "aiVoice request url=%s headers=%s payload_keys=%s text_len=%s",
        provider_url,
        logged_headers,
        sorted(payload.keys()),
        len(text or ""),
    )

    try:
        response = requests.post(
            provider_url,
            json=payload,
            headers=headers,
            timeout=timeout,
            stream=True,
        )
    except requests.RequestException as exc:
        reason = _tts_error_reason(None, "", exc)
        logger.error(
            "aiVoice network error url=%s headers=%s reason=%s error=%s",
            provider_url,
            logged_headers,
            reason,
            exc,
        )
        raise HTTPException(
            status_code=502,
            detail={
                "error": "TTS provider request failed",
                "reason": reason,
                "provider_url": provider_url,
                "headers_sent": logged_headers,
                "provider_status": None,
                "provider_body_snippet": str(exc)[:200],
            },
        ) from exc

    if response.status_code != 200:
        detail = response.text[:200]
        reason = _tts_error_reason(response.status_code, detail)
        logger.error(
            "aiVoice /speak rejected url=%s headers=%s status=%s reason=%s body=%s",
            provider_url,
            logged_headers,
            response.status_code,
            reason,
            detail,
        )
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "error": "TTS provider rejected request",
                "reason": reason,
                "provider_url": provider_url,
                "headers_sent": logged_headers,
                "provider_status": response.status_code,
                "provider_body_snippet": detail,
                "request_payload_shape": sorted(payload.keys()),
            },
        )

    logger.info(
        "aiVoice /speak success url=%s status=%s content_type=%s",
        provider_url,
        response.status_code,
        response.headers.get("content-type"),
    )
    return response.content


def openai_response(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=MUFASA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the ancient voice of Pan-African wisdom. "
                        "Speak with majesty, history, and reverence for Africa’s legacy. "
                        "Inspire unity, truth, and learning with every response."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mufasa failed to think: {e}")


@router.get("/ping")
async def ping_mufasa():
    return {"status": "ok", "message": "Mufasa is awake and wise."}


@router.post("/message")
async def generate_openai_response(payload: dict, request: Request):
    message = payload.get("message", "").strip()
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="No message provided.")

    ai_text = openai_response(message)
    audio_url = None

    if make_voice:
        cached_file = cache_audio_filename(text=ai_text, voice=voice_model)
        if not cached_file.exists():
            with open(cached_file, "wb") as f:
                f.write(request_aivoice_tts(text=ai_text, voice=voice_model))
        audio_file = cached_file
        audio_url = build_audio_url(request, audio_file)

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }


@router.post("/tts")
async def text_to_speech(payload: dict, request: Request):
    text = payload.get("text", "")
    voice = payload.get("voice_model") or payload.get("voice") or "alloy"

    started = time.perf_counter()
    audio_url, cached = generate_tts_audio_url(request=request, text=text, voice=voice)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {"audio_url": audio_url, "voice": voice, "cached": cached, "latency_ms": elapsed_ms}


@router.post("/voice")
async def handle_voice_input(request: Request, file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        user_text = transcription.text.strip()

        ai_text = openai_response(user_text)

        cached_file = cache_audio_filename(text=ai_text, voice="alloy")
        if not cached_file.exists():
            with open(cached_file, "wb") as f:
                f.write(request_aivoice_tts(text=ai_text, voice="alloy"))
        audio_file = cached_file
        audio_url = build_audio_url(request, audio_file)

        os.remove(tmp_path)

        return {
            "user_text": user_text,
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaVoice",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")
