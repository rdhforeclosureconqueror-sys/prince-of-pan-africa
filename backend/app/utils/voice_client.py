import httpx
import os

OPENVOICE_URL = os.getenv("OPENVOICE_URL", "https://aivoice-wmrv.onrender.com")


def _openvoice_base_url() -> str:
    base_url = OPENVOICE_URL.rstrip("/")
    for stale_path in ("/tts", "/speak"):
        if base_url.endswith(stale_path):
            return base_url[: -len(stale_path)]
    return base_url


async def text_to_speech(text: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{_openvoice_base_url()}/speak",
            json={"text": text, "voice": "alloy", "format": "mp3"},
        )
        res.raise_for_status()
        return {"audio": res.content, "content_type": res.headers.get("content-type", "audio/mpeg")}


async def speech_to_text(audio_url: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{OPENVOICE_URL}/stt", json={"url": audio_url})
        return res.json()
