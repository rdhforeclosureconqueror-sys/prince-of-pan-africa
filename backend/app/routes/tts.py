from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["TTS"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    style: str = "strong"
    format: str = "mp3"


@router.post("/tts")
def tts(payload: TTSRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured for TTS.")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required for TTS.")

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=payload.voice,
            input=text,
            format=payload.format,
            instructions=f"Narration style: {payload.style}",
        )
        audio_bytes = speech.content
        media_type = "audio/mpeg" if payload.format == "mp3" else "application/octet-stream"
        return Response(content=audio_bytes, media_type=media_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {exc}")
