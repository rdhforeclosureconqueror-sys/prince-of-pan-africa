from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import requests
import os
import logging

router = APIRouter()

AIVOICE_BASE_URL = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
AIVOICE_API_KEY = os.getenv("AIVOICE_API_KEY", "")

logger = logging.getLogger("mufasa-voice")
logger.setLevel(logging.INFO)


class TTSRequest(BaseModel):
    text: str
    format: str | None = "mp3"
    voice: str | None = "alloy"


def _aivoice_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if AIVOICE_API_KEY:
        headers["X-AIVOICE-KEY"] = AIVOICE_API_KEY
    return headers


@router.post("/tts")
async def proxy_tts(req: TTSRequest):
    try:
        res = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json=req.dict(),
            headers=_aivoice_headers(),
            timeout=60,
        )

        if res.status_code != 200:
            logger.error(f"TTS failed [{res.status_code}]: {res.text}")
            raise HTTPException(status_code=res.status_code, detail=res.text)

        media_type = res.headers.get("content-type", "audio/mpeg")

        def iter_bytes():
            yield res.content

        return StreamingResponse(iter_bytes(), media_type=media_type)

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


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
        return {"ok": res.status_code == 200, "status": res.status_code, "details": res.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
