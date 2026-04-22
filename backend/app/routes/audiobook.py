import hashlib
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioAsset, Audiobook, AudiobookChapter, AudiobookProgress, User
from app.routes.auth import SESSION_COOKIE
from app.routes.chat import generate_tts_audio_url, normalize_tts_text

router = APIRouter(prefix="/audiobooks", tags=["Audiobooks"])

MAX_CHARS_PER_CHAPTER = 3500
MAX_TOTAL_CHARS = 35000
MAX_TOTAL_UPLOAD_BYTES = 200_000
MAX_CONCURRENT_GENERATIONS = 2
ALLOWED_ACCESS_LEVELS = {"free", "member", "subscriber", "purchased"}

_generation_lock = threading.Lock()
_generation_counts: dict[int, int] = {}


class AudiobookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(default="Unknown", max_length=255)
    text: str = Field(min_length=1)
    voice: str = Field(default="alloy", max_length=64)
    generate_audio: bool = True
    access_level: str = Field(default="free", max_length=32)


class ProgressUpdateRequest(BaseModel):
    chapter_index: int = Field(default=0, ge=0)
    position_seconds: int = Field(default=0, ge=0)
    playback_rate: str = Field(default="1.0", max_length=16)


GUEST_EMAIL = "pilot.audiobook.guest@local"


def _normalize_access_level(value: str) -> str:
    normalized = (value or "free").strip().lower()
    if normalized not in ALLOWED_ACCESS_LEVELS:
        raise HTTPException(status_code=422, detail=f"Invalid access_level. Expected one of: {sorted(ALLOWED_ACCESS_LEVELS)}")
    return normalized


def _resolve_session_user(request: Request, db: Session) -> User | None:
    raw_user_id = request.cookies.get(SESSION_COOKIE)
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except ValueError:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


def _resolve_audiobook_user(request: Request, db: Session) -> tuple[User, bool]:
    user = _resolve_session_user(request, db)
    if user:
        return user, False

    guest_user = db.query(User).filter(User.email == GUEST_EMAIL).first()
    if guest_user:
        return guest_user, True

    guest_user = User(email=GUEST_EMAIL, password_hash="pilot-guest", role="guest")
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)
    return guest_user, True


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_into_chapters(text: str) -> list[dict]:
    clean = (text or "").replace("\r\n", "\n").strip()
    if not clean:
        return []

    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    normalized_blocks: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= MAX_CHARS_PER_CHAPTER:
            normalized_blocks.append(paragraph)
            continue

        words = paragraph.split()
        bucket: list[str] = []
        bucket_len = 0
        for word in words:
            token_len = len(word) if not bucket else len(word) + 1
            if bucket_len + token_len > MAX_CHARS_PER_CHAPTER:
                normalized_blocks.append(" ".join(bucket))
                bucket = [word]
                bucket_len = len(word)
            else:
                bucket.append(word)
                bucket_len += token_len
        if bucket:
            normalized_blocks.append(" ".join(bucket))

    chapters: list[dict] = []
    chapter_number = 1
    chunk_parts: list[str] = []
    current_len = 0

    for block in normalized_blocks:
        separator_len = 0 if not chunk_parts else 2
        if current_len + separator_len + len(block) <= MAX_CHARS_PER_CHAPTER:
            if chunk_parts:
                chunk_parts.append("\n\n")
            chunk_parts.append(block)
            current_len += separator_len + len(block)
            continue

        chapters.append({"title": f"Chapter {chapter_number}", "text": "".join(chunk_parts).strip()})
        chapter_number += 1
        chunk_parts = [block]
        current_len = len(block)

    if chunk_parts:
        chapters.append({"title": f"Chapter {chapter_number}", "text": "".join(chunk_parts).strip()})

    return chapters


def _track_generation(user_id: int, delta: int) -> None:
    with _generation_lock:
        current = _generation_counts.get(user_id, 0) + delta
        if current <= 0:
            _generation_counts.pop(user_id, None)
        else:
            _generation_counts[user_id] = current


def _ensure_generation_slot(user_id: int) -> None:
    with _generation_lock:
        current = _generation_counts.get(user_id, 0)
        if current >= MAX_CONCURRENT_GENERATIONS:
            raise HTTPException(status_code=429, detail=f"Generation limit reached. Max concurrent runs: {MAX_CONCURRENT_GENERATIONS}.")
        _generation_counts[user_id] = current + 1


def _serialize_audiobook(book: Audiobook, include_text: bool = False) -> dict:
    ordered_chapters = sorted(book.chapters, key=lambda chapter: chapter.chapter_index)
    completed_audio = sum(1 for chapter in ordered_chapters if chapter.audio_url)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "voice": book.voice,
        "source_type": book.source_type,
        "access_level": book.access_level,
        "status": book.status,
        "chapter_count": book.chapter_count,
        "audio_chapter_count": completed_audio,
        "total_characters": book.total_characters,
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "chapters": [
            {
                "id": chapter.id,
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "character_count": chapter.character_count,
                "status": chapter.status,
                "audio_url": chapter.audio_url,
                **({"text": chapter.text} if include_text else {}),
            }
            for chapter in ordered_chapters
        ],
    }


def _generate_audio_for_book(*, request: Request, db: Session, user: User, book: Audiobook) -> None:
    if book.status in {"completed", "audio-generated", "ready"}:
        return

    try:
        _ensure_generation_slot(user.id)
        ordered_chapters = sorted(book.chapters, key=lambda chapter: chapter.chapter_index)
        for chapter in ordered_chapters:
            if chapter.audio_url:
                if chapter.status != "completed":
                    chapter.status = "completed"
                    db.commit()
                continue

            existing_asset = db.query(AudioAsset).filter(AudioAsset.text_hash == chapter.text_hash, AudioAsset.voice == book.voice).first()
            if existing_asset:
                chapter.audio_url = existing_asset.audio_url
                chapter.status = "completed"
                chapter.audio_asset_id = existing_asset.id
                db.commit()
                continue

            chapter.status = "generating"
            db.commit()

            audio_url, _ = generate_tts_audio_url(request=request, text=chapter.text, voice=book.voice)
            asset = AudioAsset(text_hash=chapter.text_hash, voice=book.voice, audio_url=audio_url)
            db.add(asset)
            db.flush()

            chapter.audio_url = audio_url
            chapter.audio_asset_id = asset.id
            chapter.status = "completed"
            db.commit()

        book.status = "audio-generated"
        db.commit()
    except HTTPException:
        book.status = "failed"
        db.commit()
        raise
    except Exception as exc:
        book.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Audiobook generation failed: {exc}") from exc
    finally:
        _track_generation(user.id, -1)


def _create_or_reuse_audiobook(
    *, request: Request, db: Session, user: User, title: str, author: str, text: str, voice: str, source_type: str,
    generate_audio: bool, access_level: str,
) -> dict:
    normalized_text = normalize_tts_text(text)
    if not normalized_text:
        raise HTTPException(status_code=400, detail="Text is required.")
    if len(normalized_text) > MAX_TOTAL_CHARS:
        raise HTTPException(status_code=413, detail=f"Total characters exceed limit ({MAX_TOTAL_CHARS}).")

    normalized_access = _normalize_access_level(access_level)
    content_hash = _hash_text(f"{title.strip()}|{author.strip()}|{normalized_text}")
    existing = db.query(Audiobook).filter(Audiobook.user_id == user.id, Audiobook.content_hash == content_hash, Audiobook.voice == voice).first()
    if existing:
        if generate_audio and existing.status in {"draft", "queued", "failed"}:
            existing.status = "generating"
            db.commit()
            _generate_audio_for_book(request=request, db=db, user=user, book=existing)
            db.refresh(existing)
        return {"cached": True, "audiobook": _serialize_audiobook(existing)}

    chapters = _split_into_chapters(normalized_text)
    if not chapters:
        raise HTTPException(status_code=400, detail="Unable to generate chapters from text.")

    initial_status = "generating" if generate_audio else "draft"
    chapter_status = "queued" if generate_audio else "draft"
    book = Audiobook(
        user_id=user.id,
        title=title.strip(),
        author=author.strip() or "Unknown",
        source_type=source_type,
        source_text=normalized_text,
        content_hash=content_hash,
        voice=voice,
        access_level=normalized_access,
        status=initial_status,
        total_characters=len(normalized_text),
        chapter_count=len(chapters),
    )
    db.add(book)
    db.flush()

    for index, chapter in enumerate(chapters, start=1):
        text_value = chapter["text"].strip()
        db.add(AudiobookChapter(
            audiobook_id=book.id,
            chapter_index=index,
            title=chapter["title"],
            text=text_value,
            text_hash=_hash_text(text_value),
            character_count=len(text_value),
            status=chapter_status,
        ))

    db.add(AudiobookProgress(audiobook_id=book.id, user_id=user.id, chapter_index=0, position_seconds=0, playback_rate="1.0", updated_at=datetime.utcnow()))
    db.commit()
    db.refresh(book)

    if generate_audio:
        _generate_audio_for_book(request=request, db=db, user=user, book=book)

    db.refresh(book)
    return {"cached": False, "audiobook": _serialize_audiobook(book)}


@router.post("/create")
def create_audiobook(payload: AudiobookCreateRequest, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    return _create_or_reuse_audiobook(
        request=request,
        db=db,
        user=user,
        title=payload.title,
        author=payload.author,
        text=payload.text,
        voice=payload.voice,
        source_type="paste",
        generate_audio=payload.generate_audio,
        access_level=payload.access_level,
    )


@router.post("/upload")
async def upload_audiobook(
    request: Request,
    title: str = Form(...),
    author: str = Form("Unknown"),
    voice: str = Form("alloy"),
    access_level: str = Form("free"),
    generate_audio: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user, _ = _resolve_audiobook_user(request, db)
    filename = (file.filename or "").lower()
    if not filename.endswith(".txt"):
        raise HTTPException(status_code=415, detail="Only .txt uploads are supported in V1.")

    payload = await file.read()
    if len(payload) > MAX_TOTAL_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload size exceeds limit ({MAX_TOTAL_UPLOAD_BYTES} bytes).")

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Text file must be UTF-8 encoded.") from exc

    return _create_or_reuse_audiobook(
        request=request,
        db=db,
        user=user,
        title=title,
        author=author,
        text=text,
        voice=voice,
        source_type="upload",
        generate_audio=generate_audio,
        access_level=access_level,
    )


@router.get("")
def list_audiobooks(request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    books = db.query(Audiobook).filter(Audiobook.user_id == user.id).order_by(Audiobook.created_at.desc()).all()
    return {"items": [_serialize_audiobook(book) for book in books]}


@router.get("/{audiobook_id}")
def get_audiobook(audiobook_id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")

    progress = db.query(AudiobookProgress).filter(AudiobookProgress.audiobook_id == audiobook_id, AudiobookProgress.user_id == user.id).first()
    return {
        **_serialize_audiobook(book, include_text=True),
        "progress": {
            "chapter_index": progress.chapter_index if progress else 0,
            "position_seconds": progress.position_seconds if progress else 0,
            "playback_rate": progress.playback_rate if progress else "1.0",
        },
    }


@router.post("/{audiobook_id}/generate-audio")
def generate_audio_for_saved_book(audiobook_id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")

    if book.status in {"generating"}:
        return {"ok": True, "status": book.status, "audiobook": _serialize_audiobook(book)}

    book.status = "generating"
    db.commit()
    _generate_audio_for_book(request=request, db=db, user=user, book=book)
    db.refresh(book)
    return {"ok": True, "status": book.status, "audiobook": _serialize_audiobook(book)}


@router.post("/{audiobook_id}/progress")
def update_progress(audiobook_id: int, payload: ProgressUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")

    progress = db.query(AudiobookProgress).filter(AudiobookProgress.audiobook_id == audiobook_id, AudiobookProgress.user_id == user.id).first()
    if not progress:
        progress = AudiobookProgress(audiobook_id=audiobook_id, user_id=user.id)
        db.add(progress)

    progress.chapter_index = payload.chapter_index
    progress.position_seconds = payload.position_seconds
    progress.playback_rate = payload.playback_rate
    progress.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
