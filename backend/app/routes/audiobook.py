import hashlib
import re
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioAsset, Audiobook, AudiobookChapter, AudiobookChapterReflection, AudiobookProgress, User
from app.routes.auth import SESSION_COOKIE
from app.routes.chat import generate_tts_audio_url, normalize_tts_text

router = APIRouter(prefix="/audiobooks", tags=["Audiobooks"])

MAX_CHARS_PER_CHAPTER = 3500
MAX_INGEST_TOTAL_CHARS = 1_200_000
MAX_SEGMENT_PASS_CHARS = 42_000
MAX_TOTAL_UPLOAD_BYTES = 1_600_000
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
    completed_chapters: list[int] = Field(default_factory=list)


class ReflectionRequest(BaseModel):
    notes: str = Field(default="", max_length=5000)
    skipped: bool = False


class ReflectionSummaryRequest(BaseModel):
    include_skipped: bool = False


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


def _chunk_text_block(block_text: str) -> list[str]:
    if not block_text.strip():
        return []

    words = block_text.strip().split()
    chunks: list[str] = []
    bucket: list[str] = []
    bucket_len = 0
    for word in words:
        token_len = len(word) if not bucket else len(word) + 1
        if bucket and bucket_len + token_len > MAX_CHARS_PER_CHAPTER:
            chunks.append(" ".join(bucket))
            bucket = [word]
            bucket_len = len(word)
        else:
            bucket.append(word)
            bucket_len += token_len

    if bucket:
        chunks.append(" ".join(bucket))

    return chunks


def _split_block_in_batches(text: str) -> list[str]:
    if len(text) <= MAX_SEGMENT_PASS_CHARS:
        return [text]

    batches: list[str] = []
    start = 0
    while start < len(text):
        upper = min(len(text), start + MAX_SEGMENT_PASS_CHARS)
        if upper < len(text):
            pivot = text.rfind("\n\n", start, upper)
            if pivot <= start:
                pivot = text.rfind(". ", start, upper)
            if pivot <= start:
                pivot = upper
            batches.append(text[start:pivot].strip())
            start = pivot
        else:
            batches.append(text[start:upper].strip())
            start = upper
    return [segment for segment in batches if segment]


def _chapter_heading(line: str) -> str | None:
    normalized = (line or "").strip()
    if not normalized or len(normalized) > 120:
        return None
    chapter_pattern = re.compile(
        r"^(chapter|part|book|section|act)\s+([0-9ivxlcdm]+|[a-zA-Z][a-zA-Z0-9\-]*)"
        r"([:\-–]\s*.+)?$",
        re.IGNORECASE,
    )
    if chapter_pattern.match(normalized):
        return normalized
    return None


def _split_into_chapters(text: str) -> tuple[list[dict], str]:
    clean = (text or "").replace("\r\n", "\n").strip()
    if not clean:
        return [], "empty"

    ingest_segments = _split_block_in_batches(clean)
    full_lines: list[str] = []
    for segment in ingest_segments:
        full_lines.extend(segment.split("\n"))

    sections: list[dict] = []
    current_title = "Opening"
    current_lines: list[str] = []
    found_heading = False

    for raw_line in full_lines:
        heading = _chapter_heading(raw_line)
        if heading:
            found_heading = True
            if current_lines:
                sections.append({"title": current_title, "text": "\n".join(current_lines).strip()})
                current_lines = []
            current_title = heading
            continue
        current_lines.append(raw_line)

    if current_lines:
        sections.append({"title": current_title, "text": "\n".join(current_lines).strip()})

    if not found_heading:
        sections = [{"title": "Chapter 1", "text": clean}]

    chapters: list[dict] = []
    for section in sections:
        section_title = section["title"].strip() or "Chapter"
        paragraphs = [p.strip() for p in section["text"].split("\n\n") if p.strip()]
        if not paragraphs:
            continue

        chunk_parts: list[str] = []
        current_len = 0
        local_part = 1

        for paragraph in paragraphs:
            paragraph_chunks = _chunk_text_block(paragraph)
            for block in paragraph_chunks:
                separator_len = 0 if not chunk_parts else 2
                if chunk_parts and current_len + separator_len + len(block) > MAX_CHARS_PER_CHAPTER:
                    title = section_title if local_part == 1 else f"{section_title} (Part {local_part})"
                    chapters.append({"title": title, "text": "\n\n".join(chunk_parts).strip()})
                    chunk_parts = []
                    current_len = 0
                    local_part += 1
                    separator_len = 0
                chunk_parts.append(block)
                current_len += separator_len + len(block)

        if chunk_parts:
            title = section_title if local_part == 1 else f"{section_title} (Part {local_part})"
            chapters.append({"title": title, "text": "\n\n".join(chunk_parts).strip()})
    strategy = "detected_headings" if found_heading else "auto_partitioned"
    return chapters, strategy


def _reflection_prompt(book_title: str, chapter_title: str, chapter_index: int) -> str:
    return (
        f"After Chapter {chapter_index} ({chapter_title}) of {book_title}, "
        "what one idea felt most transformative, and how will you apply it this week?"
    )


def _build_reflection_summary(*, reflections: list[AudiobookChapterReflection], include_skipped: bool) -> str:
    scoped = [item for item in reflections if include_skipped or not item.skipped]
    noted = [item for item in scoped if item.notes.strip()]
    if not noted:
        return "No reflection notes have been saved yet."

    snippets = []
    for item in noted:
        first_line = item.notes.strip().splitlines()[0][:220]
        snippets.append(f"Chapter {item.chapter_index}: {first_line}")

    joined = "\n".join(f"- {line}" for line in snippets[:24])
    return (
        "Reflection Recap\n"
        f"Captured entries: {len(noted)}\n\n"
        f"{joined}\n\n"
        "Common thread: your notes repeatedly emphasize application, identity, and sustained practice."
    )


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
        "segmentation_strategy": book.source_type if book.source_type.startswith("segmented:") else "legacy",
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
    if len(normalized_text) > MAX_INGEST_TOTAL_CHARS:
        raise HTTPException(status_code=413, detail=f"Total characters exceed safe ingest limit ({MAX_INGEST_TOTAL_CHARS}).")

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

    chapters, segmentation_strategy = _split_into_chapters(normalized_text)
    if not chapters:
        raise HTTPException(status_code=400, detail="Unable to generate chapters from text.")

    initial_status = "generating" if generate_audio else "draft"
    chapter_status = "queued" if generate_audio else "draft"
    book = Audiobook(
        user_id=user.id,
        title=title.strip(),
        author=author.strip() or "Unknown",
        source_type=f"segmented:{source_type}:{segmentation_strategy}",
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

    db.add(AudiobookProgress(
        audiobook_id=book.id,
        user_id=user.id,
        chapter_index=0,
        position_seconds=0,
        playback_rate="1.0",
        completed_chapters=[],
        updated_at=datetime.utcnow(),
    ))
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
            "completed_chapters": progress.completed_chapters if progress else [],
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
    progress.completed_chapters = sorted(set([idx for idx in payload.completed_chapters if idx >= 1]))
    progress.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.get("/{audiobook_id}/reflections")
def list_reflections(audiobook_id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")

    reflections = (
        db.query(AudiobookChapterReflection)
        .filter(AudiobookChapterReflection.audiobook_id == audiobook_id, AudiobookChapterReflection.user_id == user.id)
        .order_by(AudiobookChapterReflection.chapter_index.asc())
        .all()
    )
    return {
        "items": [
            {
                "chapter_index": item.chapter_index,
                "prompt": item.prompt,
                "notes": item.notes,
                "skipped": bool(item.skipped),
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in reflections
        ]
    }


@router.put("/{audiobook_id}/chapters/{chapter_index}/reflection")
def save_reflection(audiobook_id: int, chapter_index: int, payload: ReflectionRequest, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")
    if chapter_index < 1 or chapter_index > book.chapter_count:
        raise HTTPException(status_code=422, detail="Invalid chapter index.")

    chapter = db.query(AudiobookChapter).filter(AudiobookChapter.audiobook_id == audiobook_id, AudiobookChapter.chapter_index == chapter_index).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found.")

    prompt = _reflection_prompt(book.title, chapter.title, chapter_index)
    record = (
        db.query(AudiobookChapterReflection)
        .filter(
            AudiobookChapterReflection.audiobook_id == audiobook_id,
            AudiobookChapterReflection.user_id == user.id,
            AudiobookChapterReflection.chapter_index == chapter_index,
        )
        .first()
    )
    if not record:
        record = AudiobookChapterReflection(
            audiobook_id=audiobook_id,
            user_id=user.id,
            chapter_index=chapter_index,
            prompt=prompt,
            notes=payload.notes.strip(),
            skipped=payload.skipped,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(record)
    else:
        record.prompt = prompt
        record.notes = payload.notes.strip()
        record.skipped = payload.skipped
        record.updated_at = datetime.utcnow()

    db.commit()
    return {"ok": True, "chapter_index": chapter_index, "prompt": prompt}


@router.post("/{audiobook_id}/reflections/summary")
def summarize_reflections(audiobook_id: int, payload: ReflectionSummaryRequest, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")

    reflections = (
        db.query(AudiobookChapterReflection)
        .filter(AudiobookChapterReflection.audiobook_id == audiobook_id, AudiobookChapterReflection.user_id == user.id)
        .order_by(AudiobookChapterReflection.chapter_index.asc())
        .all()
    )
    summary = _build_reflection_summary(reflections=reflections, include_skipped=payload.include_skipped)
    return {"summary": summary, "count": len(reflections)}
