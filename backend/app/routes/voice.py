from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
import requests
import os
import logging

router = APIRouter()

SKILL_WORLD_TTS_URL = (
    os.getenv("SKILL_WORLD_TTS_URL")
    or os.getenv("AIVOICE_BASE_URL")
    or os.getenv("OPENVOICE_URL")
    or "https://aivoice-wmrv.onrender.com/speak"
)
AIVOICE_BASE_URL = (
    os.getenv("AIVOICE_BASE_URL")
    or os.getenv("OPENVOICE_URL")
    or "https://aivoice-wmrv.onrender.com"
)
AIVOICE_API_KEY = os.getenv("AIVOICE_API_KEY", "")

logger = logging.getLogger("mufasa-voice")
logger.setLevel(logging.INFO)


class TTSRequest(BaseModel):
    text: str
    format: str | None = "mp3"
    voice: str | None = "alloy"
    speed: float | None = None
    pitch: float | None = None


def _aivoice_tts_headers() -> dict:
    return {"Content-Type": "application/json"}


def _aivoice_base_url() -> str:
    configured_url = (SKILL_WORLD_TTS_URL or AIVOICE_BASE_URL).rstrip("/")
    for stale_path in ("/tts", "/speak"):
        if configured_url.endswith(stale_path):
            return configured_url[: -len(stale_path)]
    return configured_url


def _aivoice_speak_url() -> str:
    configured_url = (SKILL_WORLD_TTS_URL or AIVOICE_BASE_URL).rstrip("/")
    if configured_url.endswith("/speak"):
        return configured_url
    if configured_url.endswith("/tts"):
        return f"{configured_url[:-len('/tts')]}/speak"
    return f"{configured_url}/speak"


def _tts_payload(req: TTSRequest) -> dict:
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    payload = {"text": text}
    for key in ("voice", "format", "speed", "pitch"):
        value = getattr(req, key)
        if value is not None:
            payload[key] = value
    return payload


@router.post("/tts")
async def proxy_tts(req: TTSRequest):
    provider_url = _aivoice_speak_url()
    payload = _tts_payload(req)
    headers = _aivoice_tts_headers()
    auth_header_sent = False
    logger.info(
        "aiVoice TTS upstream request url=%s method=POST auth_header_sent=%s payload_keys=%s text_len=%s",
        provider_url,
        auth_header_sent,
        sorted(payload.keys()),
        len(payload.get("text", "")),
    )
    try:
        res = requests.post(
            provider_url,
            json=payload,
            headers=headers,
            timeout=60,
        )
    except requests.RequestException as e:
        logger.error(
            "aiVoice TTS upstream network error url=%s method=POST auth_header_sent=%s error=%s",
            provider_url,
            auth_header_sent,
            e,
        )
        raise HTTPException(status_code=502, detail=f"TTS upstream request failed: {e}") from e

    media_type = res.headers.get("content-type", "audio/mpeg")
    if res.status_code != 200:
        detail = res.text[:500]
        mismatch = (
            " production aiVoice behavior does not match the repo truth report."
            if res.status_code == 401 and "missing_internal_token" in detail.lower()
            else ""
        )
        logger.error(
            "aiVoice TTS upstream response url=%s method=POST auth_header_sent=%s status=%s content_type=%s body=%s",
            provider_url,
            auth_header_sent,
            res.status_code,
            media_type,
            detail,
        )
        raise HTTPException(status_code=res.status_code, detail=f"{detail}{mismatch}")

    logger.info(
        "aiVoice TTS upstream response url=%s method=POST auth_header_sent=%s status=%s content_type=%s",
        provider_url,
        auth_header_sent,
        res.status_code,
        media_type,
    )
    return Response(content=res.content, media_type=media_type, status_code=res.status_code)


@router.post("/stt")
async def proxy_stt(file: UploadFile = File(...)):
    try:
        files = {"file": (file.filename, await file.read(), file.content_type)}

        res = requests.post(
            f"{AIVOICE_BASE_URL}/stt",
            files=files,
            headers={"X-AIVOICE-KEY": AIVOICE_API_KEY} if AIVOICE_API_KEY else {},
            timeout=90,
        )

        if res.status_code != 200:
            logger.error(f"STT failed [{res.status_code}]: {res.text}")
            raise HTTPException(status_code=res.status_code, detail=res.text)

        return JSONResponse(res.json())

    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")


@router.get("/health")
def health():
    try:
        res = requests.get(
            f"{AIVOICE_BASE_URL}/health",
            headers={"X-AIVOICE-KEY": AIVOICE_API_KEY} if AIVOICE_API_KEY else {},
            timeout=10,
        )
        return {
            "ok": res.status_code == 200,
            "status": res.status_code,
            "provider_base_url": AIVOICE_BASE_URL,
            "provider_key_present": bool(AIVOICE_API_KEY),
            "details": res.json(),
        }
    except Exception as e:
        return {
            "ok": False,
            "provider_base_url": AIVOICE_BASE_URL,
            "provider_key_present": bool(AIVOICE_API_KEY),
            "error": str(e),
        }
