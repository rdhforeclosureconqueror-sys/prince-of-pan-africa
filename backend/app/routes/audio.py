import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioAsset, Audiobook, AudiobookChapter
from app.routes.audiobook import _resolve_audiobook_user, _hash_text
from app.routes.chat import STATIC_AUDIO_DIR, generate_tts_audio_url, infer_audio_format_from_url

router = APIRouter(prefix="/api/audio", tags=["Audio Assets"])

SUPPORTED_AUDIO_FORMATS = {"mp3", "m4a", "wav"}
CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
}


class SaveAudioRequest(BaseModel):
    bookId: int = Field(ge=1)
    chapterId: int = Field(ge=1)
    title: str | None = Field(default=None, max_length=255)
    voice: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    audioUrl: str | None = None
    duration: int | None = Field(default=None, ge=0)
    format: str | None = Field(default="mp3", max_length=16)


class RegenerateAudioRequest(BaseModel):
    bookId: int = Field(ge=1)
    chapterId: int = Field(ge=1)
    confirm: bool = False


def slugify(value: str, fallback: str = "audio") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or fallback


def clean_audio_filename(book: Audiobook, chapter: AudiobookChapter, audio_format: str) -> str:
    return f"{slugify(book.title, 'book')}-chapter-{chapter.chapter_index:02d}-{slugify(chapter.title, 'chapter')}.{audio_format}"


def storage_key_from_url(audio_url: str | None) -> str | None:
    if not audio_url:
        return None
    path = audio_url.split("?", 1)[0]
    marker = "/static/audio/"
    if marker in path:
        return f"audio/{path.rsplit(marker, 1)[1]}"
    return path.rstrip("/").rsplit("/", 1)[-1] or None


def local_audio_path(asset: AudioAsset) -> Path:
    key = (asset.storage_key or storage_key_from_url(asset.audio_url) or "").lstrip("/")
    filename = key.split("/", 1)[1] if key.startswith("audio/") else Path(key).name
    if not filename:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")
    path = STATIC_AUDIO_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")
    return path


def serialize_audio_asset(asset: AudioAsset, book: Audiobook | None = None, chapter: AudiobookChapter | None = None) -> dict:
    audio_format = (asset.format or infer_audio_format_from_url(asset.audio_url) or "mp3").lower()
    if audio_format not in SUPPORTED_AUDIO_FORMATS:
        audio_format = "mp3"
    filename = asset.filename
    if not filename and book and chapter:
        filename = clean_audio_filename(book, chapter, audio_format)
    return {
        "id": asset.id,
        "audioId": asset.id,
        "bookId": asset.audiobook_id or (book.id if book else None),
        "chapterId": asset.chapter_id or (chapter.id if chapter else None),
        "title": asset.title or (chapter.title if chapter else None),
        "voice": asset.voice,
        "model": asset.model or asset.voice,
        "duration": asset.duration_seconds,
        "format": audio_format,
        "createdAt": asset.created_at.isoformat() if asset.created_at else None,
        "audioUrl": asset.audio_url,
        "storageKey": asset.storage_key or storage_key_from_url(asset.audio_url),
        "filename": filename,
        "downloadUrl": f"/api/audio/download/{asset.id}",
    }


def find_saved_asset(db: Session, book: Audiobook, chapter: AudiobookChapter, voice: str) -> AudioAsset | None:
    return (
        db.query(AudioAsset)
        .filter(AudioAsset.chapter_id == chapter.id, AudioAsset.audiobook_id == book.id, AudioAsset.voice == voice)
        .first()
        or db.query(AudioAsset).filter(AudioAsset.text_hash == chapter.text_hash, AudioAsset.voice == voice).first()
    )


def attach_asset_metadata(db: Session, asset: AudioAsset, book: Audiobook, chapter: AudiobookChapter, *, duration: int | None = None, audio_format: str | None = None) -> AudioAsset:
    normalized_format = (audio_format or asset.format or infer_audio_format_from_url(asset.audio_url) or "mp3").lower()
    if normalized_format not in SUPPORTED_AUDIO_FORMATS:
        normalized_format = "mp3"
    asset.audiobook_id = book.id
    asset.chapter_id = chapter.id
    asset.title = chapter.title
    asset.model = asset.model or book.voice
    asset.duration_seconds = duration if duration is not None else asset.duration_seconds
    asset.format = normalized_format
    asset.storage_key = asset.storage_key or storage_key_from_url(asset.audio_url)
    asset.filename = clean_audio_filename(book, chapter, normalized_format)
    chapter.audio_asset_id = asset.id
    chapter.audio_url = asset.audio_url
    chapter.status = "completed"
    db.commit()
    db.refresh(asset)
    return asset


def get_owned_book_chapter(db: Session, request: Request, book_id: int, chapter_id: int) -> tuple[Audiobook, AudiobookChapter]:
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == book_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")
    chapter = db.query(AudiobookChapter).filter(AudiobookChapter.id == chapter_id, AudiobookChapter.audiobook_id == book.id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    return book, chapter


@router.post("/save")
def save_audio(payload: SaveAudioRequest, request: Request, db: Session = Depends(get_db)):
    book, chapter = get_owned_book_chapter(db, request, payload.bookId, payload.chapterId)
    voice = (payload.voice or book.voice or "alloy").strip()
    audio_url = payload.audioUrl or chapter.audio_url
    if not audio_url:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")

    asset = find_saved_asset(db, book, chapter, voice)
    if not asset:
        asset = AudioAsset(
            text_hash=chapter.text_hash or _hash_text(chapter.text),
            voice=voice,
            audio_url=audio_url,
            audiobook_id=book.id,
            chapter_id=chapter.id,
        )
        db.add(asset)
        db.flush()

    if payload.title:
        chapter.title = payload.title.strip() or chapter.title
    asset.audio_url = audio_url
    asset.model = payload.model or asset.model or voice
    saved = attach_asset_metadata(db, asset, book, chapter, duration=payload.duration, audio_format=payload.format)
    return {"ok": True, "audio": serialize_audio_asset(saved, book, chapter), "message": "Audio saved."}


@router.get("/book/{book_id}/chapter/{chapter_id}")
def get_chapter_audio(book_id: int, chapter_id: int, request: Request, db: Session = Depends(get_db)):
    book, chapter = get_owned_book_chapter(db, request, book_id, chapter_id)
    asset = find_saved_asset(db, book, chapter, book.voice)
    if not asset:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")
    if chapter.audio_asset_id != asset.id or chapter.audio_url != asset.audio_url:
        attach_asset_metadata(db, asset, book, chapter)
    return {"ok": True, "audio": serialize_audio_asset(asset, book, chapter), "message": "Saved audio already exists. Use saved audio or regenerate?"}


@router.get("/download/{audio_id}")
def download_audio(audio_id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    asset = db.query(AudioAsset).filter(AudioAsset.id == audio_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")
    book = db.query(Audiobook).filter(Audiobook.id == asset.audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")
    chapter = db.query(AudiobookChapter).filter(AudiobookChapter.id == asset.chapter_id, AudiobookChapter.audiobook_id == book.id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="No saved audio found for this chapter.")

    path = local_audio_path(asset)
    audio_format = (asset.format or infer_audio_format_from_url(asset.audio_url) or path.suffix.lstrip(".") or "mp3").lower()
    filename = asset.filename or clean_audio_filename(book, chapter, audio_format)
    return FileResponse(
        path,
        media_type=CONTENT_TYPES.get(audio_format, "audio/mpeg"),
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/regenerate")
def regenerate_audio(payload: RegenerateAudioRequest, request: Request, db: Session = Depends(get_db)):
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Regenerating may use a new AI voice request. Continue?")
    book, chapter = get_owned_book_chapter(db, request, payload.bookId, payload.chapterId)
    audio_url, cached = generate_tts_audio_url(request=None, text=chapter.text, voice=book.voice, base_url=str(request.base_url), force=True)
    asset = find_saved_asset(db, book, chapter, book.voice)
    if not asset:
        asset = AudioAsset(text_hash=chapter.text_hash, voice=book.voice, audio_url=audio_url)
        db.add(asset)
        db.flush()
    asset.audio_url = audio_url
    saved = attach_asset_metadata(db, asset, book, chapter, audio_format="mp3")
    return {"ok": True, "regenerated": True, "provider_called": not cached, "audio": serialize_audio_asset(saved, book, chapter)}
