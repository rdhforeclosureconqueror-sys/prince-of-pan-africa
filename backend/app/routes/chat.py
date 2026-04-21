from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import OpenAI
import requests
import tempfile
import os
import uuid
import logging
from pathlib import Path
from app.config import settings

router = APIRouter()

STATIC_AUDIO_DIR = Path("app/static/audio")
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


def generate_audio_filename(ext="mp3"):
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"


def save_audio_file(audio_bytes, ext="mp3"):
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return f"/static/audio/{filename.name}"


def request_aivoice_tts(*, text: str, voice: str, timeout: int = 45):
    payload = {"text": text, "format": "mp3", "voice": voice}
    try:
        response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json=payload,
            headers=aivoice_headers(),
            timeout=timeout,
            stream=True,
        )
    except requests.RequestException as exc:
        logger.error("aiVoice network error base_url=%s error=%s", AIVOICE_BASE_URL, exc)
        raise HTTPException(
            status_code=502,
            detail=f"aiVoice unreachable at {AIVOICE_BASE_URL}: {exc}",
        ) from exc

    if response.status_code != 200:
        detail = response.text[:250]
        logger.error(
            "aiVoice /tts rejected status=%s base_url=%s body=%s",
            response.status_code,
            AIVOICE_BASE_URL,
            detail,
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=f"aiVoice /tts rejected request ({response.status_code}): {detail}",
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
async def generate_openai_response(payload: dict):
    message = payload.get("message", "").strip()
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="No message provided.")

    ai_text = openai_response(message)
    audio_url = None

    if make_voice:
        audio_url = save_audio_file(request_aivoice_tts(text=ai_text, voice=voice_model))

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }


@router.post("/tts")
async def text_to_speech(payload: dict):
    text = payload.get("text", "").strip()
    voice = payload.get("voice_model", "alloy")

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    audio_url = save_audio_file(request_aivoice_tts(text=text, voice=voice))
    return {"audio_url": audio_url, "voice": voice}


@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...)):
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

        audio_url = save_audio_file(request_aivoice_tts(text=ai_text, voice="alloy"))

        os.remove(tmp_path)

        return {
            "user_text": user_text,
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaVoice",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")
