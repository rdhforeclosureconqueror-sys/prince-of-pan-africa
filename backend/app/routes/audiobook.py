import hashlib
import mimetypes
import html
import io
import logging
import os
import re
import threading
import time
import zipfile
from pathlib import Path
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import PlainTextResponse
from pypdf import PdfReader
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.dependencies.auth import require_permission
from app.models import AudioAsset, Audiobook, AudiobookChapter, AudiobookChapterReflection, AudiobookProgress, BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User, compute_text_checksum
from app.config import settings
from app.session import SESSION_COOKIE, parse_session_cookie_value, should_use_secure_cookie
from app.routes.chat import generate_tts_audio_url, infer_audio_format_from_url, normalize_tts_text

router = APIRouter(prefix="/audiobooks", tags=["Audiobooks"])

MAX_CHARS_PER_CHAPTER = 3500
MAX_INGEST_TOTAL_CHARS = 1_200_000
MAX_SEGMENT_PASS_CHARS = 42_000
MAX_TOTAL_UPLOAD_BYTES = 1_600_000
MAX_CONCURRENT_GENERATIONS = 2
MAX_GENERATION_JOB_SECONDS = 900
ALLOWED_ACCESS_LEVELS = {"free", "member", "subscriber", "purchased"}

DEFAULT_COVER_IMAGE_PATH = "/book-covers/library-placeholder.svg"
MAX_COVER_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
ALLOWED_COVER_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
BOOK_COVER_STORAGE_DIR = Path(settings.BOOK_COVER_STORAGE_DIR).expanduser()


def _cover_storage_dir() -> Path:
    BOOK_COVER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return BOOK_COVER_STORAGE_DIR


def _is_safe_svg(payload: bytes) -> bool:
    head = payload[:4096].decode("utf-8", errors="ignore").lower()
    if "<svg" not in head:
        return False
    blocked = ("<script", "javascript:", "<foreignobject", " onload=", " onerror=", " onclick=", " data:text/html")
    return not any(item in head for item in blocked)


def _validate_cover_upload(file: UploadFile, payload: bytes) -> str:
    original_name = file.filename or "cover"
    suffix = Path(original_name).suffix.lower()
    content_type = (file.content_type or mimetypes.guess_type(original_name)[0] or "").lower()
    if suffix not in ALLOWED_COVER_EXTENSIONS or content_type not in ALLOWED_COVER_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Cover image must be a JPG, JPEG, PNG, WEBP, or safe SVG file.")
    if not payload:
        raise HTTPException(status_code=422, detail="Cover image cannot be empty.")
    if len(payload) > MAX_COVER_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Cover image exceeds limit ({MAX_COVER_UPLOAD_BYTES} bytes).")

    signatures = {
        ".jpg": payload.startswith(b"\xff\xd8\xff"),
        ".jpeg": payload.startswith(b"\xff\xd8\xff"),
        ".png": payload.startswith(b"\x89PNG\r\n\x1a\n"),
        ".webp": payload.startswith(b"RIFF") and payload[8:12] == b"WEBP",
        ".svg": _is_safe_svg(payload),
    }
    if not signatures.get(suffix, False):
        raise HTTPException(status_code=415, detail="Cover image content does not match an allowed image type.")
    return suffix


async def _save_cover_upload(file: UploadFile | None) -> str:
    if not file or not file.filename:
        return DEFAULT_COVER_IMAGE_PATH
    payload = await file.read()
    suffix = _validate_cover_upload(file, payload)
    storage_dir = _cover_storage_dir()
    for _ in range(10):
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex}{suffix}"
        destination = storage_dir / filename
        try:
            with destination.open("xb") as handle:
                handle.write(payload)
            return f"/static/book-covers/{filename}"
        except FileExistsError:
            continue
    raise HTTPException(status_code=500, detail="Could not reserve a unique cover filename.")

_generation_lock = threading.Lock()
_generation_counts: dict[int, int] = {}
_book_generation_threads: dict[int, threading.Thread] = {}
_book_generation_state: dict[int, dict] = {}

logger = logging.getLogger("mufasa-audiobook")


class AudiobookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(default="Unknown", max_length=255)
    description: str = Field(default="", max_length=2000)
    cover_image_path: str = Field(default=DEFAULT_COVER_IMAGE_PATH, max_length=500)
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

class OrganizerTextIngestRequest(BaseModel):
    title: str = Field(default="Untitled", min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=1_200_000)

class OrganizerPlanProposalRequest(BaseModel):
    document_id: int = Field(ge=1)
    plan_name: str = Field(default="Default plan", min_length=1, max_length=255)
    unused_block_ids: list[str] = Field(default_factory=list)


class OrganizerPreviewRequest(BaseModel):
    document_id: int = Field(ge=1)
    plan_id: int = Field(ge=1)


class OrganizerExportRequest(OrganizerPreviewRequest):
    title: str | None = Field(default=None, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    language: str = Field(default="en", max_length=16)
    publisher: str | None = Field(default=None, max_length=255)
    copyright_year: str | None = Field(default=None, max_length=16)
    trim_size: str = Field(default="6x9", max_length=20)
    chapter_start: str = Field(default="next_page", max_length=20)

class OrganizerStructureEditRequest(BaseModel):
    document_id: int = Field(ge=1)
    plan_id: int = Field(ge=1)
    plan_name: str = Field(default="Edited plan", min_length=1, max_length=255)
    chapter_title_overrides: dict[int, str] = Field(default_factory=dict)
    merge_chapter_indexes: list[int] = Field(default_factory=list)
    split_operations: list[dict] = Field(default_factory=list)


GUEST_EMAIL = "pilot.audiobook.guest@local"
MAX_ORGANIZER_TEXT_CHARS = 1_200_000
ORGANIZER_PLAN_CHAPTER_BLOCKS = 5
BOOK_ORGANIZER_OVER_SPLIT_WARNING_THRESHOLD = 80
BOOK_ORGANIZER_OVER_SPLIT_REVIEW_THRESHOLD = 100
BOOK_ORGANIZER_MIN_CHAPTER_WORDS = 500
BOOK_ORGANIZER_EXPORT_APPROVAL_MESSAGE = "Please review and approve book structure before exporting."



@dataclass
class BookMatterItem:
    kind: str
    title: str
    body: str = ""


@dataclass
class BookSection:
    title: str
    body: str


@dataclass
class BookChapter:
    chapter_index: int
    title: str
    kind: str = "chapter"
    sections: list[BookSection] = field(default_factory=list)


@dataclass
class BookProject:
    title: str
    author: str
    language: str
    front_matter: list[BookMatterItem]
    chapters: list[BookChapter]
    subtitle: str = ""
    publisher: str = ""
    copyright_year: str = ""
    back_matter: list[BookMatterItem] = field(default_factory=list)


@dataclass
class BookExport:
    filename: str
    media_type: str
    payload: bytes

PRINT_BODY_FIRST_LINE_INDENT_PT = 14.4  # 0.2 inches at 72 points per inch.
DOCX_BODY_FIRST_LINE_INDENT_TWIPS = 288  # 0.2 inches at 1440 twips per inch.
EPUB_BODY_TEXT_INDENT = "1.2em"

BOOK_ORGANIZER_CHAPTER_WORD_NUMBERS = (
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "twenty-one", "twenty two", "thirty", "forty", "fifty",
)
BOOK_ORGANIZER_CHAPTER_MARKER_RE = re.compile(
    r"^(?P<marker>chapter\s+(?:(?:" + "|".join(re.escape(word) for word in BOOK_ORGANIZER_CHAPTER_WORD_NUMBERS) + r")|\d+|[ivxlcdm]+)|prologue|epilogue|introduction|conclusion)\s*$",
    re.IGNORECASE,
)
BOOK_ORGANIZER_SPECIAL_STRUCTURE_TYPES = {"prologue", "epilogue", "introduction", "conclusion"}


def _allow_guest_audiobooks() -> bool:
    explicit = (os.getenv("ALLOW_GUEST_AUDIOBOOKS", "") or "").strip().lower()
    if explicit in {"1", "true", "yes", "on"}:
        return True
    if explicit in {"0", "false", "no", "off"}:
        return False
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return env in {"", "local", "dev", "development", "test", "testing"} and not should_use_secure_cookie()


def _normalize_access_level(value: str) -> str:
    normalized = (value or "free").strip().lower()
    if normalized not in ALLOWED_ACCESS_LEVELS:
        raise HTTPException(status_code=422, detail=f"Invalid access_level. Expected one of: {sorted(ALLOWED_ACCESS_LEVELS)}")
    return normalized


def _resolve_session_user(request: Request, db: Session) -> User | None:
    raw_session = request.cookies.get(SESSION_COOKIE)
    if not raw_session:
        return None

    try:
        session = parse_session_cookie_value(raw_session)
    except Exception:
        return None

    user_id = session.get("user_id")
    if not user_id:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()


def _resolve_audiobook_user(request: Request, db: Session) -> tuple[User, bool]:
    user = _resolve_session_user(request, db)
    if user:
        return user, False

    if not _allow_guest_audiobooks():
        raise HTTPException(status_code=401, detail="Authentication required")

    guest_user = db.query(User).filter(User.email == GUEST_EMAIL).first()
    if guest_user:
        return guest_user, True

    guest_user = User(email=GUEST_EMAIL, password_hash="pilot-guest", role="guest")
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)
    return guest_user, True


def _auth_mode(user: User, used_guest: bool) -> str:
    if used_guest or user.role == "guest":
        return "guest"
    return "authenticated"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_paragraphs_preserving_text(text: str) -> list[str]:
    normalized = (text or "").replace("\r\n", "\n")
    paragraphs = [p for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    return paragraphs


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


def _normalize_book_manuscript_text(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _book_organizer_word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text or ""))


def _book_organizer_explicit_marker(line: str) -> str | None:
    """Return only explicit, user-facing book structure boundary markers."""
    normalized = (line or "").strip()
    if not normalized or len(normalized) > 80:
        return None
    match = BOOK_ORGANIZER_CHAPTER_MARKER_RE.match(normalized)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group("marker")).strip()


def _book_organizer_chapter_type(marker: str) -> str:
    first = (marker or "").strip().split(maxsplit=1)[0].lower()
    return first if first in BOOK_ORGANIZER_SPECIAL_STRUCTURE_TYPES else "chapter"


def _book_organizer_display_title_case(value: str) -> str:
    words = (value or "").strip().title().split()
    minor_words = {"A", "An", "And", "At", "But", "By", "For", "From", "In", "Nor", "Of", "On", "Or", "The", "To", "With"}
    adjusted = [word.lower() if index > 0 and word in minor_words else word for index, word in enumerate(words)]
    return " ".join(adjusted)


def _book_organizer_format_chapter_title(marker: str, title: str | None = None) -> str:
    marker_text = _book_organizer_display_title_case(re.sub(r"\s+", " ", (marker or "Chapter").strip()))
    title_text = _book_organizer_display_title_case((title or "").strip())
    if title_text:
        return f"{marker_text}: {title_text}"
    return marker_text


BOOK_ORGANIZER_CANONICAL_SECTION_HEADINGS = {
    "opening",
    "closing",
    "the story most people inherit",
    "slavery was wealth — but also pressure",
    "slavery was wealth - but also pressure",
}


def _book_organizer_is_title_case_heading(normalized: str) -> bool:
    words = re.findall(r"[A-Za-z][A-Za-z’'’-]*", normalized)
    if len(words) < 3 or len(words) > 10:
        return False
    if normalized.isupper():
        return False
    minor_words = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "nor", "of", "on", "or", "the", "to", "with"}
    significant_words = [word for index, word in enumerate(words) if index == 0 or word.casefold() not in minor_words]
    if len(significant_words) < 2:
        return False
    return all(word[:1].isupper() for word in significant_words)


def _book_organizer_is_section_heading(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", (line or "").strip())
    if not normalized or _book_organizer_explicit_marker(normalized):
        return False
    if normalized in {"⸻", "---", "***", "* * *"}:
        return False
    if normalized.startswith(("- ", "* ", "• ", "1. ", "—", "–")):
        return False
    if normalized[:1] in {'"', "'", "“", "‘"}:
        return False
    if len(normalized) > 90 or normalized.endswith(('.', ',', ';', ':', '?', '!')):
        return False
    words = normalized.split()
    if len(words) > 10:
        return False
    if normalized.casefold() in BOOK_ORGANIZER_CANONICAL_SECTION_HEADINGS:
        return True
    return _book_organizer_is_title_case_heading(normalized)


def _book_organizer_extract_sections(body: str) -> list[dict]:
    sections: list[dict] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for raw_line in (body or "").split("\n"):
        stripped = raw_line.strip()
        if _book_organizer_is_section_heading(stripped):
            if current_title or any(line.strip() for line in current_lines):
                sections.append({"title": current_title or "Opening", "body": "\n".join(current_lines).strip()})
            current_title = stripped
            current_lines = []
            continue
        current_lines.append(raw_line)
    if current_title or any(line.strip() for line in current_lines):
        sections.append({"title": current_title or "Opening", "body": "\n".join(current_lines).strip()})
    return sections


def _book_organizer_structure_warnings(chapter_count: int) -> list[dict]:
    warnings: list[dict] = []
    if chapter_count > BOOK_ORGANIZER_OVER_SPLIT_WARNING_THRESHOLD:
        warnings.append({
            "code": "possible_over_splitting",
            "message": "Possible over-splitting detected",
            "chapter_count": chapter_count,
        })
    if chapter_count > BOOK_ORGANIZER_OVER_SPLIT_REVIEW_THRESHOLD:
        warnings.append({
            "code": "review_required",
            "message": "Detected more than 100 chapters automatically; review before creating book formatting records.",
            "chapter_count": chapter_count,
        })
    return warnings


def _detect_book_organizer_explicit_chapters(text: str) -> list[dict]:
    clean = _normalize_book_manuscript_text(text)
    if not clean:
        return []
    lines = clean.split("\n")
    markers: list[dict] = []
    for line_index, raw_line in enumerate(lines):
        marker = _book_organizer_explicit_marker(raw_line)
        if marker:
            markers.append({"marker": marker, "line_index": line_index})
    if len(markers) < 2:
        return []

    chapters: list[dict] = []
    for idx, marker_info in enumerate(markers):
        start = marker_info["line_index"]
        end = markers[idx + 1]["line_index"] if idx + 1 < len(markers) else len(lines)
        marker = marker_info["marker"]
        content_lines = lines[start + 1:end]

        title = ""
        title_line_offset: int | None = None
        for offset, candidate in enumerate(content_lines):
            stripped = candidate.strip()
            if stripped:
                title = stripped
                title_line_offset = offset
                break

        body_lines = content_lines[(title_line_offset + 1) if title_line_offset is not None else 0:]
        body = "\n".join(body_lines).strip()
        word_count = _book_organizer_word_count(body)
        chapter_type = _book_organizer_chapter_type(marker)
        chapters.append({
            "index": len(chapters) + 1,
            "marker": marker,
            "title": title,
            "chapter_title": _book_organizer_format_chapter_title(marker, title),
            "type": chapter_type,
            "body": body,
            "sections": _book_organizer_extract_sections(body),
            "word_count": word_count,
            "warnings": [] if word_count >= BOOK_ORGANIZER_MIN_CHAPTER_WORDS or chapter_type in BOOK_ORGANIZER_SPECIAL_STRUCTURE_TYPES else [{
                "code": "short_chapter",
                "message": "Chapter is under 500 words; confirm this is an intentional book chapter.",
                "word_count": word_count,
            }],
        })
    return chapters


def _build_explicit_book_organizer_plan(blocks: list[BookOrganizerBlock], excluded_block_ids: set[str] | None = None) -> tuple[list[dict], list[dict], bool]:
    excluded = excluded_block_ids or set()
    line_entries: list[dict] = []
    for block in blocks:
        if block.block_id in excluded:
            continue
        for raw_line in (block.text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line_entries.append({"line": raw_line, "block_id": block.block_id})

    marker_positions: list[dict] = []
    for line_index, entry in enumerate(line_entries):
        marker = _book_organizer_explicit_marker(entry["line"])
        if marker:
            marker_positions.append({"marker": marker, "line_index": line_index, "block_id": entry["block_id"]})

    if len(marker_positions) < 2:
        return [], [], False

    block_order = [block.block_id for block in blocks if block.block_id not in excluded]
    block_to_index = {block_id: index for index, block_id in enumerate(block_order)}
    chapters: list[dict] = []
    warnings: list[dict] = []

    for marker_index, marker_info in enumerate(marker_positions):
        start_block_index = block_to_index[marker_info["block_id"]]
        end_block_index = (
            block_to_index[marker_positions[marker_index + 1]["block_id"]]
            if marker_index + 1 < len(marker_positions)
            else len(block_order)
        )
        chapter_block_ids = block_order[start_block_index:end_block_index]

        title = ""
        for entry in line_entries[marker_info["line_index"] + 1: marker_positions[marker_index + 1]["line_index"] if marker_index + 1 < len(marker_positions) else len(line_entries)]:
            stripped = entry["line"].strip()
            if stripped:
                title = stripped
                break

        body_text = "\n\n".join(block.text for block in blocks if block.block_id in set(chapter_block_ids))
        word_count = _book_organizer_word_count(body_text)
        chapter_type = _book_organizer_chapter_type(marker_info["marker"])
        chapter_warnings = []
        if word_count < BOOK_ORGANIZER_MIN_CHAPTER_WORDS and chapter_type not in BOOK_ORGANIZER_SPECIAL_STRUCTURE_TYPES:
            chapter_warnings.append({
                "code": "short_chapter",
                "message": "Chapter is under 500 words; confirm this is an intentional book chapter.",
                "word_count": word_count,
            })
        chapters.append({
            "chapter_index": len(chapters) + 1,
            "chapter_title": _book_organizer_format_chapter_title(marker_info["marker"], title),
            "marker": marker_info["marker"],
            "title": title,
            "type": chapter_type,
            "block_ids": chapter_block_ids,
            "word_count": word_count,
            "warnings": chapter_warnings,
        })

    warnings.extend(_book_organizer_structure_warnings(len(chapters)))
    return chapters, warnings, True

def _extract_text_from_pdf(payload: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(payload))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="This PDF could not be parsed as text.") from exc

    raw_segments: list[str] = []
    empty_pages = 0
    for page in reader.pages:
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            empty_pages += 1
            continue
        raw_segments.append(page_text)

    if not raw_segments:
        raise HTTPException(status_code=422, detail="This PDF appears to be image-based or unsupported.")

    raw_text = "\n\n".join(raw_segments)
    non_whitespace = [char for char in raw_text if not char.isspace()]
    if not non_whitespace:
        raise HTTPException(status_code=422, detail="This PDF appears to be image-based or unsupported.")

    alnum_ratio = sum(1 for char in non_whitespace if char.isalnum()) / len(non_whitespace)
    printable_ratio = sum(1 for char in non_whitespace if char.isprintable()) / len(non_whitespace)
    if len(non_whitespace) < 30 or alnum_ratio < 0.35 or printable_ratio < 0.85:
        raise HTTPException(status_code=422, detail="This PDF could not be parsed as text.")

    normalized_text = normalize_tts_text(raw_text)
    if not normalized_text:
        raise HTTPException(status_code=422, detail="This PDF could not be parsed as text.")

    if empty_pages == len(reader.pages):
        raise HTTPException(status_code=422, detail="This PDF appears to be image-based or unsupported.")

    return normalized_text


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



def _audio_storage_key(audio_url: str | None) -> str | None:
    if not audio_url:
        return None
    path = audio_url.split("?", 1)[0]
    marker = "/static/audio/"
    if marker in path:
        return f"audio/{path.rsplit(marker, 1)[1]}"
    return path.rstrip("/").rsplit("/", 1)[-1] or None


def _hydrate_audio_asset(asset: AudioAsset, book: Audiobook, chapter: AudiobookChapter, duration_seconds: int | None = None) -> AudioAsset:
    asset.audiobook_id = book.id
    asset.chapter_id = chapter.id
    asset.title = chapter.title
    asset.model = asset.model or book.voice
    asset.duration_seconds = duration_seconds if duration_seconds is not None else asset.duration_seconds
    asset.format = asset.format or infer_audio_format_from_url(asset.audio_url, fallback="mp3")
    asset.storage_key = asset.storage_key or _audio_storage_key(asset.audio_url)
    return asset


def _serialize_audio_asset(asset: AudioAsset | None, book: Audiobook | None = None, chapter: AudiobookChapter | None = None) -> dict | None:
    if not asset:
        return None
    return {
        "id": asset.id,
        "audioId": asset.id,
        "bookId": asset.audiobook_id or (book.id if book else None),
        "chapterId": asset.chapter_id or (chapter.id if chapter else None),
        "title": asset.title or (chapter.title if chapter else None),
        "voice": asset.voice,
        "model": asset.model or asset.voice,
        "duration": asset.duration_seconds,
        "format": asset.format or infer_audio_format_from_url(asset.audio_url, fallback="mp3"),
        "createdAt": asset.created_at.isoformat() if asset.created_at else None,
        "audioUrl": asset.audio_url,
        "storageKey": asset.storage_key or _audio_storage_key(asset.audio_url),
        "downloadUrl": f"/api/audio/download/{asset.id}",
    }

def _serialize_audiobook(book: Audiobook, include_text: bool = False) -> dict:
    ordered_chapters = sorted(book.chapters, key=lambda chapter: chapter.chapter_index)
    completed_audio = sum(1 for chapter in ordered_chapters if chapter.audio_url)
    progress = _build_generation_progress(book)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "cover_image_path": book.cover_image_path or DEFAULT_COVER_IMAGE_PATH,
        "cover_asset_key": book.cover_image_path or DEFAULT_COVER_IMAGE_PATH,
        "voice": book.voice,
        "source_type": book.source_type,
        "access_level": book.access_level,
        "status": book.status,
        "chapter_count": book.chapter_count,
        "audio_chapter_count": completed_audio,
        "generation_progress": progress,
        "total_characters": book.total_characters,
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "updated_at": book.updated_at.isoformat() if getattr(book, "updated_at", None) else None,
        "segmentation_strategy": book.source_type if book.source_type.startswith("segmented:") else "legacy",
        "chapters": [
            {
                "id": chapter.id,
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "character_count": chapter.character_count,
                "status": chapter.status,
                "audio_url": chapter.audio_url,
                "audio_asset_id": chapter.audio_asset_id,
                "saved_audio": (
                    _serialize_audio_asset(
                        next((asset for asset in getattr(book, "_prefetched_audio_assets", []) if asset.id == chapter.audio_asset_id), None),
                        book,
                        chapter,
                    )
                    if getattr(book, "_prefetched_audio_assets", None)
                    else (
                        {
                            "id": chapter.audio_asset_id,
                            "audioId": chapter.audio_asset_id,
                            "bookId": book.id,
                            "chapterId": chapter.id,
                            "title": chapter.title,
                            "voice": book.voice,
                            "model": book.voice,
                            "duration": None,
                            "format": infer_audio_format_from_url(chapter.audio_url, fallback="mp3"),
                            "createdAt": None,
                            "audioUrl": chapter.audio_url,
                            "storageKey": _audio_storage_key(chapter.audio_url),
                            "downloadUrl": f"/api/audio/download/{chapter.audio_asset_id}" if chapter.audio_asset_id else None,
                        }
                        if chapter.audio_asset_id and chapter.audio_url
                        else None
                    )
                ),
                **({"text": chapter.text} if include_text else {}),
            }
            for chapter in ordered_chapters
        ],
    }


def _build_generation_progress(book: Audiobook) -> dict:
    ordered_chapters = sorted(book.chapters, key=lambda chapter: chapter.chapter_index)
    total_chapters = len(ordered_chapters)
    completed_chapters = sum(1 for chapter in ordered_chapters if chapter.status == "completed")
    failed_chapters = sum(1 for chapter in ordered_chapters if chapter.status == "failed")
    generating_chapters = sum(1 for chapter in ordered_chapters if chapter.status == "generating")
    queued_chapters = sum(1 for chapter in ordered_chapters if chapter.status in {"queued", "draft"})
    current_chapter = next((chapter.chapter_index for chapter in ordered_chapters if chapter.status == "generating"), None)

    with _generation_lock:
        runtime_state = dict(_book_generation_state.get(book.id, {}))

    current_step = runtime_state.get("current_step") or book.status
    if book.status in {"queued", "draft"}:
        current_step = "pending"
    elif book.status in {"generating", "audio-generated", "ready"}:
        current_step = "generating_chapters"

    failed_chapter_indexes = [chapter.chapter_index for chapter in ordered_chapters if chapter.status == "failed"]
    runtime_errors = list(runtime_state.get("failed_chapter_errors") or [])
    runtime_error_indexes = {item.get("chapter_index") for item in runtime_errors if isinstance(item, dict)}
    failed_chapter_errors = runtime_errors + [
        {"chapter_index": chapter_index, "message": "Chapter generation failed. Please retry or regenerate this chapter."}
        for chapter_index in failed_chapter_indexes
        if chapter_index not in runtime_error_indexes
    ]

    return {
        "status": book.status,
        "current_step": current_step,
        "total_chapters": total_chapters,
        "completed_chapters": completed_chapters,
        "failed_chapters": failed_chapters,
        "failed_chapter_indexes": failed_chapter_indexes,
        "failed_chapter_errors": failed_chapter_errors,
        "generating_chapters": generating_chapters,
        "queued_chapters": queued_chapters,
        "current_chapter_index": runtime_state.get("current_chapter_index") or current_chapter,
        "message": runtime_state.get("message", ""),
        "updated_at": runtime_state.get("updated_at"),
    }


def _update_runtime_generation_state(audiobook_id: int, **state) -> None:
    with _generation_lock:
        current = dict(_book_generation_state.get(audiobook_id, {}))
        current.update(state)
        current["updated_at"] = datetime.utcnow().isoformat()
        _book_generation_state[audiobook_id] = current


def _clear_runtime_generation_state(audiobook_id: int) -> None:
    with _generation_lock:
        _book_generation_state.pop(audiobook_id, None)
        _book_generation_threads.pop(audiobook_id, None)


def _release_generation_thread(audiobook_id: int) -> None:
    with _generation_lock:
        _book_generation_threads.pop(audiobook_id, None)


def _record_chapter_generation_error(audiobook_id: int, chapter_index: int, error: Exception) -> None:
    with _generation_lock:
        current = dict(_book_generation_state.get(audiobook_id, {}))
        errors = list(current.get("failed_chapter_errors") or [])
        errors.append({
            "chapter_index": chapter_index,
            "message": str(error)[:500] or "Chapter generation failed.",
        })
        current["failed_chapter_errors"] = errors
        current["updated_at"] = datetime.utcnow().isoformat()
        _book_generation_state[audiobook_id] = current


def _generate_audio_for_book_job(*, audiobook_id: int, user_id: int, base_url: str) -> None:
    started_at = time.monotonic()
    db = SessionLocal()
    _update_runtime_generation_state(audiobook_id, current_step="generating_chapters", message="Job started", failed_chapter_errors=[])
    try:
        _ensure_generation_slot(user_id)
        book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user_id).first()
        if not book:
            return

        book.status = "generating_chapters"
        db.commit()

        ordered_chapters = sorted(book.chapters, key=lambda chapter: chapter.chapter_index)
        for chapter in ordered_chapters:
            if (time.monotonic() - started_at) > MAX_GENERATION_JOB_SECONDS:
                raise TimeoutError(f"Generation exceeded {MAX_GENERATION_JOB_SECONDS} seconds")

            if chapter.audio_url and chapter.status == "completed":
                continue

            _update_runtime_generation_state(
                audiobook_id,
                current_step="generating_chapters",
                current_chapter_index=chapter.chapter_index,
                message=f"Generating chapter {chapter.chapter_index} of {len(ordered_chapters)}",
            )
            chapter_started = time.monotonic()
            logger.info("audiobook_generation chapter_start book_id=%s chapter=%s", audiobook_id, chapter.chapter_index)

            try:
                if chapter.audio_url:
                    chapter.status = "completed"
                    db.commit()
                    continue

                existing_asset = db.query(AudioAsset).filter(AudioAsset.text_hash == chapter.text_hash, AudioAsset.voice == book.voice).first()
                if existing_asset:
                    chapter.audio_url = existing_asset.audio_url
                    chapter.status = "completed"
                    chapter.audio_asset_id = existing_asset.id
                    _hydrate_audio_asset(existing_asset, book, chapter)
                    db.commit()
                    continue

                chapter.status = "generating"
                db.commit()

                audio_url, _ = generate_tts_audio_url(request=None, text=chapter.text, voice=book.voice, base_url=base_url)
                asset = AudioAsset(text_hash=chapter.text_hash, voice=book.voice, audio_url=audio_url)
                db.add(asset)
                db.flush()
                _hydrate_audio_asset(asset, book, chapter)

                chapter.audio_url = audio_url
                chapter.audio_asset_id = asset.id
                chapter.status = "completed"
                db.commit()
                logger.info(
                    "audiobook_generation chapter_complete book_id=%s chapter=%s duration_seconds=%.2f",
                    audiobook_id,
                    chapter.chapter_index,
                    time.monotonic() - chapter_started,
                )
            except Exception as chapter_error:
                chapter.status = "failed"
                db.commit()
                _record_chapter_generation_error(audiobook_id, chapter.chapter_index, chapter_error)
                logger.exception(
                    "audiobook_generation chapter_failed book_id=%s chapter=%s error=%s",
                    audiobook_id,
                    chapter.chapter_index,
                    chapter_error,
                )

        db.refresh(book)
        failed_count = sum(1 for chapter in book.chapters if chapter.status == "failed")
        book.status = "partially_complete" if failed_count else "complete"
        db.commit()
        _update_runtime_generation_state(
            audiobook_id,
            current_step=book.status,
            message="Generation complete" if failed_count == 0 else "Generation complete with some failed chapters",
            current_chapter_index=None,
        )
    except Exception as exc:
        logger.exception("audiobook_generation job_failed book_id=%s error=%s", audiobook_id, exc)
        book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user_id).first()
        if book:
            book.status = "failed"
            db.commit()
        _update_runtime_generation_state(audiobook_id, current_step="failed", message=str(exc), current_chapter_index=None)
    finally:
        _track_generation(user_id, -1)
        db.close()
        _release_generation_thread(audiobook_id)


def _start_background_generation(*, audiobook_id: int, user_id: int, base_url: str) -> bool:
    with _generation_lock:
        active_thread = _book_generation_threads.get(audiobook_id)
        if active_thread and active_thread.is_alive():
            return False

        worker = threading.Thread(
            target=_generate_audio_for_book_job,
            kwargs={"audiobook_id": audiobook_id, "user_id": user_id, "base_url": base_url},
            daemon=True,
            name=f"audiobook-generation-{audiobook_id}",
        )
        _book_generation_threads[audiobook_id] = worker

    _update_runtime_generation_state(audiobook_id, current_step="pending", message="Job queued", current_chapter_index=None, failed_chapter_errors=[])
    worker.start()
    return True


def _create_or_reuse_audiobook(
    *, request: Request, db: Session, user: User, title: str, author: str, text: str, voice: str, source_type: str,
    generate_audio: bool, access_level: str, description: str = "", cover_image_path: str = DEFAULT_COVER_IMAGE_PATH,
) -> dict:
    ingest_started = time.monotonic()
    normalized_text = normalize_tts_text(text)
    if not normalized_text:
        raise HTTPException(status_code=400, detail="Text is required.")
    if len(normalized_text) > MAX_INGEST_TOTAL_CHARS:
        raise HTTPException(status_code=413, detail=f"Total characters exceed safe ingest limit ({MAX_INGEST_TOTAL_CHARS}).")

    normalized_access = _normalize_access_level(access_level)
    content_hash = _hash_text(f"{title.strip()}|{author.strip()}|{normalized_text}")
    existing = db.query(Audiobook).filter(Audiobook.user_id == user.id, Audiobook.content_hash == content_hash, Audiobook.voice == voice).first()
    if existing:
        should_commit = False
        normalized_cover_path = (cover_image_path or DEFAULT_COVER_IMAGE_PATH).strip()
        if normalized_cover_path != DEFAULT_COVER_IMAGE_PATH and existing.cover_image_path != normalized_cover_path:
            existing.cover_image_path = normalized_cover_path
            should_commit = True
        if generate_audio and existing.status in {"draft", "queued", "failed", "pending", "partially_complete"}:
            existing.status = "pending"
            should_commit = True
        if should_commit:
            db.commit()
        if generate_audio and existing.status in {"pending", "partially_complete"}:
            _start_background_generation(audiobook_id=existing.id, user_id=user.id, base_url=str(request.base_url))
            db.refresh(existing)
        return {"cached": True, "audiobook": _serialize_audiobook(existing)}

    segment_started = time.monotonic()
    chapters, segmentation_strategy = _split_into_chapters(normalized_text)
    logger.info(
        "audiobook_generation segmentation_complete title=%s total_chars=%s chapters=%s ingest_seconds=%.2f segment_seconds=%.2f",
        title,
        len(normalized_text),
        len(chapters),
        segment_started - ingest_started,
        time.monotonic() - segment_started,
    )
    if not chapters:
        raise HTTPException(status_code=400, detail="Unable to generate chapters from text.")

    initial_status = "pending" if generate_audio else "draft"
    chapter_status = "queued" if generate_audio else "draft"
    book = Audiobook(
        user_id=user.id,
        title=title.strip(),
        author=author.strip() or "Unknown",
        source_type=f"segmented:{source_type}:{segmentation_strategy}",
        source_text=normalized_text,
        description=(description or "").strip() or normalized_text[:280],
        cover_image_path=(cover_image_path or DEFAULT_COVER_IMAGE_PATH).strip(),
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
        _start_background_generation(audiobook_id=book.id, user_id=user.id, base_url=str(request.base_url))

    db.refresh(book)
    return {"cached": False, "audiobook": _serialize_audiobook(book)}


@router.post("/create")
async def create_audiobook(request: Request, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
    content_type = (request.headers.get("content-type") or "").lower()

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        cover_image_path = await _save_cover_upload(form.get("cover_file"))
        payload = AudiobookCreateRequest(
            title=str(form.get("title") or ""),
            author=str(form.get("author") or "Unknown"),
            description=str(form.get("description") or ""),
            cover_image_path=cover_image_path,
            text=str(form.get("text") or ""),
            voice=str(form.get("voice") or "alloy"),
            generate_audio=str(form.get("generate_audio") or "true").lower() in {"1", "true", "yes", "on"},
            access_level=str(form.get("access_level") or "free"),
        )
    else:
        payload = AudiobookCreateRequest.model_validate(await request.json())

    result = _create_or_reuse_audiobook(
        request=request,
        db=db,
        user=user,
        title=payload.title,
        author=payload.author,
        text=payload.text,
        voice=payload.voice,
        description=payload.description,
        cover_image_path=payload.cover_image_path,
        source_type="paste",
        generate_audio=payload.generate_audio,
        access_level=payload.access_level,
    )
    result["auth_mode"] = _auth_mode(user, used_guest)
    return result


@router.post("/upload")
async def upload_audiobook(
    request: Request,
    title: str = Form(...),
    author: str = Form("Unknown"),
    voice: str = Form("alloy"),
    access_level: str = Form("free"),
    generate_audio: bool = Form(True),
    file: UploadFile = File(...),
    cover_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user, used_guest = _resolve_audiobook_user(request, db)
    filename = (file.filename or "").lower()
    if not (filename.endswith(".txt") or filename.endswith(".pdf")):
        raise HTTPException(status_code=415, detail="Supported upload types are .txt and .pdf.")

    payload = await file.read()
    if len(payload) > MAX_TOTAL_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload size exceeds limit ({MAX_TOTAL_UPLOAD_BYTES} bytes).")

    if filename.endswith(".txt"):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail="Text file must be UTF-8 encoded.") from exc
    else:
        text = _extract_text_from_pdf(payload)

    cover_image_path = await _save_cover_upload(cover_file)

    result = _create_or_reuse_audiobook(
        request=request,
        db=db,
        user=user,
        title=title,
        author=author,
        text=text,
        voice=voice,
        source_type="upload",
        cover_image_path=cover_image_path,
        generate_audio=generate_audio,
        access_level=access_level,
    )
    result["auth_mode"] = _auth_mode(user, used_guest)
    return result


@router.post("/organizer/ingest-text")
def ingest_text_for_organizer(
    payload: OrganizerTextIngestRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:create_self")),
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_TEXT_BOOK_ORGANIZER:
        raise HTTPException(status_code=404, detail="Not found.")

    raw_text = payload.text or ""
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty.")
    if len(raw_text) > MAX_ORGANIZER_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Text exceeds limit ({MAX_ORGANIZER_TEXT_CHARS} characters).")

    paragraphs = _split_paragraphs_preserving_text(raw_text)
    if not paragraphs:
        raise HTTPException(status_code=422, detail="Text must include at least one paragraph.")

    source_hash = compute_text_checksum(raw_text)
    document = BookOrganizerDocument(
        user_id=user.id,
        title=payload.title.strip() or "Untitled",
        source_text_hash=source_hash,
    )
    db.add(document)
    db.flush()

    created_blocks: list[BookOrganizerBlock] = []
    for index, paragraph_text in enumerate(paragraphs, start=1):
        block = BookOrganizerBlock(
            document_id=document.id,
            block_index=index,
            block_id=f"p{index:05d}",
            text=paragraph_text,
            checksum=compute_text_checksum(paragraph_text),
        )
        db.add(block)
        created_blocks.append(block)

    db.commit()
    db.refresh(document)
    return {
        "document": {
            "id": document.id,
            "title": document.title,
            "user_id": document.user_id,
            "source_text_hash": document.source_text_hash,
            "created_at": document.created_at.isoformat(),
        },
        "blocks": [
            {"block_id": block.block_id, "block_index": block.block_index, "checksum": block.checksum}
            for block in created_blocks
        ],
    }


@router.post("/organizer/propose-plan")
def propose_organization_plan(
    payload: OrganizerPlanProposalRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:update_self")),
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_TEXT_BOOK_ORGANIZER:
        raise HTTPException(status_code=404, detail="Not found.")

    document = (
        db.query(BookOrganizerDocument)
        .filter(BookOrganizerDocument.id == payload.document_id, BookOrganizerDocument.user_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    blocks = (
        db.query(BookOrganizerBlock)
        .filter(BookOrganizerBlock.document_id == document.id)
        .order_by(BookOrganizerBlock.block_index.asc())
        .all()
    )
    if not blocks:
        raise HTTPException(status_code=422, detail="Document has no blocks.")

    existing_ids = [b.block_id for b in blocks]
    existing_set = set(existing_ids)
    requested_unused = list(dict.fromkeys(payload.unused_block_ids or []))
    invalid_unused = [block_id for block_id in requested_unused if block_id not in existing_set]
    if invalid_unused:
        raise HTTPException(status_code=422, detail={"invalid_block_ids": invalid_unused})

    unused_set = set(requested_unused)
    used_ids = [block_id for block_id in existing_ids if block_id not in unused_set]
    chapters, warnings, explicit_mode = _build_explicit_book_organizer_plan(blocks, unused_set)
    if not explicit_mode:
        chapters = []
        for start in range(0, len(used_ids), ORGANIZER_PLAN_CHAPTER_BLOCKS):
            chunk = used_ids[start : start + ORGANIZER_PLAN_CHAPTER_BLOCKS]
            chapters.append(
                {
                    "chapter_index": len(chapters) + 1,
                    "chapter_title": f"Chapter {len(chapters) + 1}",
                    "type": "chapter",
                    "block_ids": chunk,
                }
            )
        warnings = _book_organizer_structure_warnings(len(chapters))

    if requested_unused:
        warnings.append(
            {
                "code": "unused_blocks",
                "message": "Some blocks were explicitly marked unused.",
                "block_ids": requested_unused,
            }
        )

    structure = {
        "title_candidate": document.title.strip() or "Untitled",
        "chapters": chapters,
        "chapter_count": len(chapters),
        "detection_mode": "explicit_chapter_markers" if explicit_mode else "paragraph_chunks",
        "requires_review": True,
        "review_status": "pending",
        "approved": False,
        "warnings": warnings,
    }

    plan = BookOrganizationPlan(
        document_id=document.id,
        name=payload.plan_name.strip() or "Default plan",
        structure=structure,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {"plan_id": plan.id, "document_id": document.id, "structure": structure}


def _validate_plan_block_ids(chapters: list[dict], block_map: dict[str, BookOrganizerBlock]):
    missing_block_ids: list[str] = []
    for chapter in chapters:
        for block_id in chapter.get("block_ids", []):
            if block_id not in block_map:
                missing_block_ids.append(block_id)
    if missing_block_ids:
        raise HTTPException(status_code=422, detail={"invalid_block_ids": list(dict.fromkeys(missing_block_ids))})


def _clean_organizer_chapter_paragraphs(chapter: dict, raw_paragraphs: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    marker = chapter.get("marker")
    title = chapter.get("title")
    chapter_title = chapter.get("chapter_title")
    marker_removed = not marker
    title_removed = not title
    chapter_title_removed = not chapter_title
    for paragraph in raw_paragraphs:
        lines = (paragraph.get("text", "") or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and not marker_removed and _book_organizer_explicit_marker(lines[0]) == marker:
            lines.pop(0)
            marker_removed = True
            while lines and not lines[0].strip():
                lines.pop(0)
        if lines and not title_removed and lines[0].strip().casefold() == str(title).strip().casefold():
            lines.pop(0)
            title_removed = True
            while lines and not lines[0].strip():
                lines.pop(0)
        if lines and not chapter_title_removed and lines[0].strip().casefold() == str(chapter_title).strip().casefold():
            lines.pop(0)
            chapter_title_removed = True
            while lines and not lines[0].strip():
                lines.pop(0)
        text = "\n".join(lines).strip()
        if text:
            cleaned.append({**paragraph, "text": text})
    return cleaned


def _build_organizer_chapters_from_plan(plan: BookOrganizationPlan, block_map: dict[str, BookOrganizerBlock]) -> list[dict]:
    _validate_plan_block_ids(plan.structure.get("chapters", []), block_map)
    chapters = []
    for chapter in plan.structure.get("chapters", []):
        raw_paragraphs = []
        for block_id in chapter.get("block_ids", []):
            block = block_map.get(block_id)
            if compute_text_checksum(block.text) != block.checksum:
                raise HTTPException(status_code=422, detail={"checksum_mismatch_block_ids": [block.block_id]})
            raw_paragraphs.append({"block_id": block.block_id, "block_index": block.block_index, "text": block.text})

        paragraphs = _clean_organizer_chapter_paragraphs(chapter, raw_paragraphs)
        body_text = "\n\n".join(paragraph["text"] for paragraph in paragraphs)
        chapters.append(
            {
                "chapter_index": chapter.get("chapter_index"),
                "chapter_title": chapter.get("chapter_title"),
                "marker": chapter.get("marker"),
                "title": chapter.get("title"),
                "type": chapter.get("type", "chapter"),
                "word_count": _book_organizer_word_count(body_text),
                "warnings": chapter.get("warnings", []),
                "paragraphs": paragraphs,
                "sections": _book_organizer_extract_sections(body_text),
            }
        )
    return chapters

def _safe_export_basename(title: str | None, fallback: str = "manuscript") -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", (title or fallback)).strip("_") or fallback


def _clean_metadata_value(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _copyright_notice(project: BookProject) -> str:
    if not project.copyright_year:
        return "Copyright ©. All rights reserved."
    holder = project.author or project.publisher or project.title
    return f"Copyright © {project.copyright_year} {holder}. All rights reserved."


def _resolve_organizer_export_project(
    *,
    payload: OrganizerExportRequest | OrganizerPreviewRequest,
    user: User,
    db: Session,
    author: str | None = None,
    language: str | None = None,
) -> tuple[BookOrganizerDocument, BookOrganizationPlan, BookProject]:
    if not settings.ENABLE_TEXT_BOOK_ORGANIZER:
        raise HTTPException(status_code=404, detail="Not found.")
    document = (
        db.query(BookOrganizerDocument)
        .filter(BookOrganizerDocument.id == payload.document_id, BookOrganizerDocument.user_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    plan = (
        db.query(BookOrganizationPlan)
        .filter(BookOrganizationPlan.id == payload.plan_id, BookOrganizationPlan.document_id == document.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    blocks = (
        db.query(BookOrganizerBlock)
        .filter(BookOrganizerBlock.document_id == document.id)
        .order_by(BookOrganizerBlock.block_index.asc())
        .all()
    )
    block_map = {block.block_id: block for block in blocks}
    approved = bool(plan.structure.get("approved") or plan.structure.get("review_status") == "approved")
    if not approved:
        chapter_count = len(plan.structure.get("chapters", []))
        logger.warning(
            "organizer_export_blocked document_id=%s plan_id=%s chapter_count=%s epilogue_count=%s source_text_checksum=%s review_status=%s approved=%s",
            document.id,
            plan.id,
            chapter_count,
            len([chapter for chapter in plan.structure.get("chapters", []) if chapter.get("type") == "epilogue"]),
            document.source_text_hash,
            plan.structure.get("review_status", "pending"),
            approved,
        )
        raise HTTPException(status_code=400, detail=BOOK_ORGANIZER_EXPORT_APPROVAL_MESSAGE)
    chapter_dicts = _build_organizer_chapters_from_plan(plan, block_map)
    title = _clean_metadata_value(getattr(payload, "title", None) or plan.structure.get("title_candidate") or document.title or "Untitled") or "Untitled"
    subtitle = _clean_metadata_value(getattr(payload, "subtitle", None))
    author_name = _clean_metadata_value(author or getattr(payload, "author", None))
    if not author_name:
        author_name = "Unknown"
    language_code = _clean_metadata_value(language or getattr(payload, "language", None) or "en") or "en"
    publisher = _clean_metadata_value(getattr(payload, "publisher", None))
    copyright_year = _clean_metadata_value(getattr(payload, "copyright_year", None))
    copyright_body = _copyright_notice(
        BookProject(
            title=title,
            subtitle=subtitle,
            author=author_name,
            language=language_code,
            publisher=publisher,
            copyright_year=copyright_year,
            front_matter=[],
            chapters=[],
        )
    )
    project = BookProject(
        title=title,
        subtitle=subtitle,
        author=author_name,
        language=language_code,
        publisher=publisher,
        copyright_year=copyright_year,
        front_matter=[
            BookMatterItem(kind="title_page", title=title, body="\n".join(part for part in [subtitle, f"by {author_name}"] if part)),
            BookMatterItem(kind="copyright", title="Copyright", body=copyright_body),
            BookMatterItem(kind="toc", title="Table of Contents", body=""),
        ],
        chapters=[
            BookChapter(
                chapter_index=int(chapter.get("chapter_index") or index),
                title=(chapter.get("chapter_title") or f"Chapter {index}").strip(),
                kind=chapter.get("type", "chapter"),
                sections=[BookSection(title=section.get("title") or "Opening", body=section.get("body") or "") for section in chapter.get("sections", [])],
            )
            for index, chapter in enumerate(chapter_dicts, start=1)
        ],
    )
    return document, plan, _sanitize_export_project(project)


def _log_organizer_export(
    *,
    document: BookOrganizerDocument,
    plan: BookOrganizationPlan,
    project: BookProject,
    export_format: str,
) -> None:
    logger.info(
        "organizer_export document_id=%s plan_id=%s chapter_count=%s epilogue_count=%s source_text_checksum=%s review_status=%s approved=%s export_format=%s",
        document.id,
        plan.id,
        len(project.chapters),
        len([chapter for chapter in project.chapters if chapter.kind == "epilogue"]),
        document.source_text_hash,
        plan.structure.get("review_status", "pending"),
        bool(plan.structure.get("approved") or plan.structure.get("review_status") == "approved"),
        export_format,
    )

def _canonical_plaintext(project: BookProject) -> str:
    project = _sanitize_export_project(project)
    parts: list[str] = []
    for chapter in project.chapters:
        parts.append(chapter.title)
        for section in chapter.sections:
            if section.title:
                parts.append(section.title.strip())
            if section.body.strip():
                parts.append(_normalize_dividers_for_text(section.body.strip()))
        parts.append("")
    return "\n\n".join(parts).rstrip() + "\n"


def _normalize_dividers_for_text(text: str) -> str:
    lines = []
    for line in (text or "").split("\n"):
        if line.strip() in {"⸻", "---", "***", "* * *"}:
            lines.append("***")
        else:
            lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _normalize_heading_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().casefold())


def _strip_leading_chapter_heading(text: str, chapter_title: str) -> str:
    """Remove duplicated canonical chapter headings from exported body text.

    The renderer owns chapter titles. Source blocks can still include the same
    title as the first body line, especially after explicit chapter detection or
    review edits. Strip only leading exact canonical matches so intentional
    later references remain untouched.
    """
    if not (text or "").strip() or not chapter_title.strip():
        return text or ""
    lines = (text or "").splitlines()
    title_key = _normalize_heading_for_compare(chapter_title)
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    while start < len(lines) and _normalize_heading_for_compare(lines[start]) == title_key:
        start += 1
        while start < len(lines) and not lines[start].strip():
            start += 1
    return "\n".join(lines[start:]).strip()


def _sanitize_export_project(project: BookProject) -> BookProject:
    sanitized_chapters: list[BookChapter] = []
    for chapter in project.chapters:
        sanitized_sections: list[BookSection] = []
        stripped_heading = False
        for section in chapter.sections:
            body = section.body or ""
            if not stripped_heading and body.strip():
                body = _strip_leading_chapter_heading(body, chapter.title)
                stripped_heading = True
            sanitized_sections.append(BookSection(title=section.title, body=body))
        sanitized_chapters.append(
            BookChapter(
                chapter_index=chapter.chapter_index,
                title=chapter.title,
                kind=chapter.kind,
                sections=sanitized_sections,
            )
        )
    return BookProject(
        title=project.title,
        subtitle=project.subtitle,
        author=project.author,
        language=project.language,
        publisher=project.publisher,
        copyright_year=project.copyright_year,
        front_matter=list(project.front_matter),
        chapters=sanitized_chapters,
        back_matter=list(project.back_matter),
    )


def _clean_export_text(text: str) -> str:
    return (text or "").replace("\t", " ")


def _iter_export_blocks(text: str) -> list[tuple[str, str | list[str]]]:
    blocks: list[tuple[str, str | list[str]]] = []
    normalized_text = _normalize_dividers_for_text(_clean_export_text(text))
    for para in re.split(r"\n\s*\n", normalized_text):
        stripped = para.strip()
        if not stripped:
            continue
        if stripped == "***":
            blocks.append(("divider", "***"))
            continue
        lines = [line.strip() for line in stripped.split("\n") if line.strip()]
        if lines and all(line.startswith(("- ", "* ", "• ")) for line in lines):
            blocks.append(("list", [line[2:].strip() if line[:2] in {"- ", "* ", "• "} else line.lstrip("-*• ").strip() for line in lines]))
            continue
        blocks.append(("paragraph", stripped))
    return blocks


def _canonical_markdown(project: BookProject) -> str:
    project = _sanitize_export_project(project)
    title_parts = [f"# {project.title}"]
    if project.subtitle:
        title_parts.append(project.subtitle)
    title_parts.append(f"by {project.author}")
    parts = [*title_parts, "", _copyright_notice(project), "", "## Table of Contents"]
    parts.extend(f"- {chapter.title}" for chapter in project.chapters)
    for chapter in project.chapters:
        parts.extend(["", f"## {chapter.title}"])
        for section in chapter.sections:
            if section.title:
                parts.append(f"### {section.title}")
            if section.body.strip():
                parts.append(_normalize_dividers_for_text(section.body.strip()))
    return "\n\n".join(part for part in parts if part is not None).rstrip() + "\n"


def _docx_paragraph(text: str, style: str | None = None, page_break_before: bool = False) -> str:
    props = ""
    if style:
        props += f'<w:pStyle w:val="{style}"/>'
    if page_break_before:
        props += '<w:pageBreakBefore/>'
    ppr = f"<w:pPr>{props}</w:pPr>" if props else ""
    runs = []
    for index, line in enumerate(_clean_export_text(text).split("\n")):
        if index:
            runs.append("<w:r><w:br/></w:r>")
        runs.append(f'<w:r><w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r>')
    return f"<w:p>{ppr}{''.join(runs)}</w:p>"


def _build_docx_export(project: BookProject) -> bytes:
    project = _sanitize_export_project(project)
    title_page = [_docx_paragraph(project.title, "Title")]
    if project.subtitle:
        title_page.append(_docx_paragraph(project.subtitle, "Subtitle"))
    title_page.append(_docx_paragraph(f"by {project.author}", "Subtitle"))
    body = [
        *title_page,
        _docx_paragraph(_copyright_notice(project), "BodyFirst", True),
        *([_docx_paragraph(f"Publisher: {project.publisher}", "Body")] if project.publisher else []),
        _docx_paragraph("Table of Contents", "Heading1", True),
        _docx_paragraph("Update this placeholder in your word processor after opening the manuscript.", "BodyFirst"),
    ]
    for chapter in project.chapters:
        body.append(_docx_paragraph(chapter.title, "Heading1", True))
        next_paragraph_style = "BodyFirst"
        for section in chapter.sections:
            if section.title:
                body.append(_docx_paragraph(section.title, "Heading2"))
                next_paragraph_style = "BodyFirst"
            for block_type, block_body in _iter_export_blocks(section.body):
                if block_type == "list":
                    for item in block_body:
                        body.append(_docx_paragraph(f"• {item}", "ListParagraph"))
                    next_paragraph_style = "Body"
                elif block_type == "divider":
                    body.append(_docx_paragraph("•  •  •", "Divider"))
                    next_paragraph_style = "BodyFirst"
                else:
                    body.append(_docx_paragraph(str(block_body), next_paragraph_style))
                    next_paragraph_style = "Body"
    sect = '<w:sectPr><w:pgSz w:w="8640" w:h="12960"/><w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="540" w:footer="720" w:gutter="0"/></w:sectPr>'
    document_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + ''.join(body) + sect + '</w:body></w:document>'
    styles_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="0" w:line="276" w:lineRule="auto"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Body"><w:name w:val="Body"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:firstLine="{DOCX_BODY_FIRST_LINE_INDENT_TWIPS}"/><w:spacing w:before="0" w:after="0" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="BodyFirst"><w:name w:val="Body First"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:firstLine="0"/><w:spacing w:before="0" w:after="0" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:outlineLvl w:val="0"/><w:jc w:val="center"/><w:spacing w:before="240" w:after="240"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:outlineLvl w:val="1"/><w:jc w:val="center"/><w:spacing w:before="180" w:after="120"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Divider"><w:name w:val="Ornamental Divider"/><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360" w:hanging="180"/><w:spacing w:before="0" w:after="0" w:line="276" w:lineRule="auto"/></w:pPr></w:style>
</w:styles>'''
    subject = project.subtitle or project.title
    keywords = "; ".join(part for part in [project.language, project.publisher] if part)
    core_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{xml_escape(project.title)}</dc:title><dc:subject>{xml_escape(subject)}</dc:subject><dc:creator>{xml_escape(project.author)}</dc:creator><cp:keywords>{xml_escape(keywords)}</cp:keywords><dc:language>{xml_escape(project.language)}</dc:language><cp:category>{xml_escape(project.publisher)}</cp:category><cp:lastModifiedBy>{xml_escape(project.author)}</cp:lastModifiedBy></cp:coreProperties>'
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
        zf.writestr("word/_rels/document.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("docProps/core.xml", core_xml)
    return bio.getvalue()


def _epub_xhtml(title: str, body: str, language: str = "en") -> str:
    safe_language = html.escape(language or "en")
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<!DOCTYPE html>'
        f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{safe_language}" lang="{safe_language}">'
        f'<head><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>'
        f'<body>{body}</body></html>'
    )


def _epub_toc_chapters(project: BookProject) -> list[BookChapter]:
    return [chapter for chapter in project.chapters if chapter.kind in {"chapter", "epilogue"}]


def _build_epub_export(project: BookProject) -> bytes:
    project = _sanitize_export_project(project)
    uid = hashlib.sha1(f"{project.title}:{project.author}".encode()).hexdigest()
    toc_chapters = _epub_toc_chapters(project)
    nav_items = ''.join(f'<li><a href="chapter-{chapter.chapter_index}.xhtml">{html.escape(chapter.title)}</a></li>' for chapter in toc_chapters)
    manifest_items = ''.join(f'<item id="chap{chapter.chapter_index}" href="chapter-{chapter.chapter_index}.xhtml" media-type="application/xhtml+xml"/>' for chapter in project.chapters)
    spine_items = ''.join(f'<itemref idref="chap{chapter.chapter_index}"/>' for chapter in project.chapters)
    nav_points = ''.join(
        f'<navPoint id="navPoint-{position}" playOrder="{position}"><navLabel><text>{xml_escape(chapter.title)}</text></navLabel><content src="chapter-{chapter.chapter_index}.xhtml"/></navPoint>'
        for position, chapter in enumerate(toc_chapters, start=1)
    )
    nav = _epub_xhtml("Table of Contents", f'<nav epub:type="toc" id="toc"><h1>Table of Contents</h1><ol>{nav_items}</ol></nav>', project.language)
    optional_metadata = ""
    if project.subtitle:
        optional_metadata += f'<dc:description>{xml_escape(project.subtitle)}</dc:description>'
    if project.publisher:
        optional_metadata += f'<dc:publisher>{xml_escape(project.publisher)}</dc:publisher>'
    if project.copyright_year:
        optional_metadata += f'<dc:rights>{xml_escape(_copyright_notice(project))}</dc:rights>'
    package = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:uuid:{uid}</dc:identifier><dc:title>{xml_escape(project.title)}</dc:title><dc:creator>{xml_escape(project.author)}</dc:creator><dc:language>{xml_escape(project.language)}</dc:language>{optional_metadata}<meta property="dcterms:modified">{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="style" href="style.css" media-type="text/css"/>{manifest_items}</manifest><spine toc="ncx"><itemref idref="nav" linear="no"/>{spine_items}</spine></package>'''
    ncx = f'''<?xml version="1.0" encoding="UTF-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:{uid}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head><docTitle><text>{xml_escape(project.title)}</text></docTitle><navMap>{nav_points}</navMap></ncx>'''
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", package, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", ncx, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr(
            "OEBPS/style.css",
            (
                "body{font-family:serif;line-height:1.45;margin:1em;}"
                "h1{font-size:1.6em;line-height:1.2;text-align:center;margin:2.2em 0 1em;}"
                "h2{font-size:1.2em;line-height:1.25;text-align:center;margin:1.4em 0 .6em;}"
                f"p{{margin:0;text-indent:{EPUB_BODY_TEXT_INDENT};}}"
                "h1+p,h2+p,.section-divider+p{ text-indent:0;}"
                ".section-divider{text-align:center;text-indent:0;margin:1.2em 0;}"
                "ul{margin:.6em 0 .6em 1.25em;}"
            ),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for chapter in project.chapters:
            body_parts = [f'<h1>{html.escape(chapter.title)}</h1>']
            for section in chapter.sections:
                if section.title:
                    body_parts.append(f'<h2>{html.escape(section.title)}</h2>')
                for block_type, block_body in _iter_export_blocks(section.body):
                    if block_type == "divider":
                        body_parts.append('<p class="section-divider">***</p>')
                    elif block_type == "list":
                        items = ''.join(f'<li>{html.escape(item)}</li>' for item in block_body)
                        body_parts.append(f"<ul>{items}</ul>")
                    else:
                        body_parts.append(f"<p>{html.escape(str(block_body)).replace(chr(10), '<br/>')}</p>")
            zf.writestr(f"OEBPS/chapter-{chapter.chapter_index}.xhtml", _epub_xhtml(chapter.title, ''.join(body_parts), project.language), compress_type=zipfile.ZIP_DEFLATED)
    return bio.getvalue()


def _pdf_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_literal_bytes(text: str) -> bytes:
    encoded = (text or "").encode("cp1252", errors="replace")
    out = bytearray(b"(")
    for value in encoded:
        if value in (40, 41, 92) or value < 32 or value > 126:
            out.extend(f"\\{value:03o}".encode("ascii"))
        else:
            out.append(value)
    out.extend(b")")
    return bytes(out)


def _wrap_pdf_text(text: str, max_chars: int = 72) -> list[str]:
    wrapped: list[str] = []
    for para in re.split(r"\n\s*\n", text or ""):
        words = para.replace("\n", " ").split()
        line = ""
        for word in words:
            if line and len(line) + len(word) + 1 > max_chars:
                wrapped.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            wrapped.append(line)
        wrapped.append("")
    return wrapped


def _estimate_pdf_text_width(text: str, size: int = 11, font: str = "R") -> float:
    width_units = 0.0
    for char in text or "":
        if char == " ":
            width_units += 0.25
        elif char in ".,:;?!\'\"-–—":
            width_units += 0.28
        elif char in "ilI1|":
            width_units += 0.25
        elif char in "mwMW":
            width_units += 0.82
        elif char.isupper():
            width_units += 0.68
        elif char.islower():
            width_units += 0.48
        else:
            width_units += 0.5
    if font == "B":
        width_units *= 1.04
    elif font == "I":
        width_units *= 0.98
    return width_units * size


def _wrap_pdf_text_to_width(text: str, max_width: float, size: int = 11, font: str = "R") -> list[str]:
    lines: list[str] = []
    for para in re.split(r"\n\s*\n", _clean_export_text(text)):
        words = para.replace("\n", " ").split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and _estimate_pdf_text_width(candidate, size, font) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return lines


def _wrap_pdf_paragraph_to_width(text: str, max_width: float, first_line_indent: float = 0, size: int = 11, font: str = "R") -> list[str]:
    words = _clean_export_text(text).replace("\n", " ").split()
    lines: list[str] = []
    line = ""
    line_width = max_width - first_line_indent
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and _estimate_pdf_text_width(candidate, size, font) > line_width:
            lines.append(line)
            line = word
            line_width = max_width
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _add_wrapped_pdf_lines(add_line, text: str, size: int = 11, indent: int = 0, max_chars: int = 70) -> None:
    for line in _wrap_pdf_text(text, max_chars):
        add_line(line, size, indent)


def _build_pdf_export(project: BookProject, trim_size: str = "6x9", chapter_start: str = "next_page") -> bytes:
    project = _sanitize_export_project(project)
    width, height = (432, 648) if trim_size == "6x9" else (432, 648)
    # 6x9 print PDF: left/right margins are both above KDP's 0.5-inch
    # gutter guidance for a ~189-page book, and bottom text margin clears the footer.
    margin_left, margin_right, margin_top, margin_bottom = 60, 54, 78, 84
    header_y = height - 44
    footer_y = 34
    body_text_width = width - margin_left - margin_right
    max_body_chars = 62
    chapter_title_size = 19
    chapter_title_leading = 24
    chapter_title_block_width = min(width - margin_left - margin_right - 48, 270)
    chapter_title_top_gap = 34
    chapter_title_to_section_gap = 14
    section_to_body_gap = 6
    chapter_start_mode = "right_hand" if chapter_start == "right_hand" else "next_page"
    page_records: list[dict] = []
    current: list[tuple[str, int, float, float, str]] = []
    y = height - margin_top

    def has_visible_lines(lines: list[tuple[str, int, float, float, str]] | None = None) -> bool:
        return any(line[0].strip() for line in (current if lines is None else lines))

    def commit_page(show_number: bool = True, number: int | None = None, running_header: str = "") -> None:
        nonlocal current
        if has_visible_lines():
            page_records.append({"lines": current, "show_number": show_number, "number": number, "running_header": running_header})
        current = []

    def add_line(text: str, size: int = 11, indent: int = 0, align: str = "left", font: str = "R", leading: float | None = None):
        nonlocal y
        line_height = leading if leading is not None else size + 5
        if y < margin_bottom:
            commit_page()
            y = height - margin_top
        if not text.strip() and not has_visible_lines():
            y -= line_height
            return
        if align == "center":
            approx_width = _estimate_pdf_text_width(text, size, font)
            x = max(margin_left, min(width - margin_right - approx_width, (width - approx_width) / 2))
        elif align == "right":
            approx_width = _estimate_pdf_text_width(text, size, font)
            x = max(margin_left, width - margin_right - approx_width)
        else:
            x = margin_left + indent
        current.append((text, size, x, y, font))
        y -= line_height

    def build_toc_pages(chapter_starts: dict[int, int]) -> list[dict]:
        nonlocal current, y
        saved_current, saved_y = current, y
        toc_pages: list[dict] = []
        current = []
        y = height - margin_top

        add_line("Table of Contents", 18, align="center", font="B", leading=24)
        add_line("")
        for chapter in project.chapters:
            page_number = str(chapter_starts.get(chapter.chapter_index, ""))
            label = chapter.title
            dots = "." * max(3, 56 - len(label) - len(page_number))
            add_line(f"{label} {dots} {page_number}", 11)
        if has_visible_lines():
            toc_pages.append({"lines": current, "show_number": False, "number": None, "running_header": ""})
        current, y = saved_current, saved_y
        return toc_pages

    # Title page: no visible page number, with a print-book hierarchy.
    y = height / 2 + 82
    add_line(project.title, 24, align="center", font="B", leading=30)
    if project.subtitle:
        add_line(project.subtitle, 15, align="center", font="I", leading=22)
    y -= 16
    add_line(f"by {project.author}", 13, align="center", leading=20)
    commit_page(show_number=False)

    # Copyright page: no visible page number and exact user-provided publisher metadata.
    y = height - margin_top
    add_line("Copyright", 18, align="center", font="B", leading=24)
    add_line("")
    _add_wrapped_pdf_lines(add_line, _copyright_notice(project), 11, max_chars=max_body_chars)
    if project.publisher:
        _add_wrapped_pdf_lines(add_line, f"Publisher: {project.publisher}", 11, max_chars=max_body_chars)
    commit_page(show_number=False)

    # Body pages are built separately so body numbering starts at Chapter One.
    body_pages: list[dict] = []
    chapter_starts: dict[int, int] = {}
    current = []
    y = height - margin_top
    active_header = ""
    current_body_running_header = ""

    def commit_body_page(show_number: bool = True) -> None:
        nonlocal current
        if has_visible_lines():
            body_pages.append({
                "lines": current,
                "show_number": show_number,
                "number": len([page for page in body_pages if page.get("show_number")]) + 1 if show_number else None,
                "running_header": current_body_running_header,
            })
        current = []

    def add_blank_verso_page() -> None:
        body_pages.append({"lines": [], "show_number": False, "number": None, "running_header": ""})

    def new_body_page():
        nonlocal y, current_body_running_header
        commit_body_page()
        current_body_running_header = active_header
        y = height - margin_top

    def add_body_line(text: str, size: int = 11, indent: int = 0, align: str = "left", font: str = "R", leading: float | None = None):
        nonlocal y
        line_height = leading if leading is not None else size + 5
        if y < margin_bottom:
            new_body_page()
        if not text.strip() and not has_visible_lines():
            y -= line_height
            return
        if align == "center":
            approx_width = _estimate_pdf_text_width(text, size, font)
            x = max(margin_left, min(width - margin_right - approx_width, (width - approx_width) / 2))
        elif align == "right":
            approx_width = _estimate_pdf_text_width(text, size, font)
            x = max(margin_left, width - margin_right - approx_width)
        else:
            x = margin_left + indent
        current.append((text, size, x, y, font))
        y -= line_height

    for chapter in project.chapters:
        if current:
            new_body_page()
        active_header = chapter.title
        current_body_running_header = ""
        if chapter_start_mode == "right_hand" and len(body_pages) % 2 == 1:
            add_blank_verso_page()
        chapter_starts[chapter.chapter_index] = len([page for page in body_pages if page.get("show_number")]) + 1
        y -= chapter_title_top_gap
        chapter_title_lines = _wrap_pdf_text_to_width(chapter.title, chapter_title_block_width, chapter_title_size, "B") or [chapter.title]
        for title_line in chapter_title_lines:
            add_body_line(title_line, chapter_title_size, align="center", font="B", leading=chapter_title_leading)
        y -= chapter_title_to_section_gap
        for section_index, section in enumerate(chapter.sections):
            next_paragraph_flush_left = True
            if section.title:
                if section_index:
                    y -= 6
                add_body_line(section.title, 13, align="center", font="B", leading=19)
                y -= section_to_body_gap
            for block_type, block_body in _iter_export_blocks(section.body):
                if block_type == "divider":
                    y -= 3
                    add_body_line("•  •  •", 12, align="center", leading=19)
                    y -= 3
                    next_paragraph_flush_left = True
                    continue
                if block_type == "list":
                    for item in block_body:
                        list_lines = _wrap_pdf_paragraph_to_width(str(item), body_text_width - 20, size=11)
                        for wrapped_index, line in enumerate(list_lines):
                            prefix = "• " if wrapped_index == 0 else "  "
                            add_body_line(f"{prefix}{line}", 11, indent=20, leading=16)
                    y -= 4
                    next_paragraph_flush_left = False
                    continue
                first_line_indent = 0 if next_paragraph_flush_left else PRINT_BODY_FIRST_LINE_INDENT_PT
                paragraph_lines = _wrap_pdf_paragraph_to_width(str(block_body), body_text_width, first_line_indent, size=11)
                for wrapped_index, line in enumerate(paragraph_lines):
                    add_body_line(line, 11, indent=first_line_indent if wrapped_index == 0 else 0, leading=16)
                next_paragraph_flush_left = False
    commit_body_page()

    page_records.extend(build_toc_pages(chapter_starts))
    page_records.extend(body_pages)

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(len(page_records)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_records)} >>".encode())
    for i, page in enumerate(page_records):
        page_lines = page["lines"]
        page_obj = 3 + i * 2
        content_obj = page_obj + 1
        stream_parts = [b"BT /F1 11 Tf"]
        header = (page.get("running_header") or "").strip()
        if page.get("show_number") and header:
            stream_parts.append(b"/F3 8 Tf " + f"{margin_left:.0f} {header_y:.0f}".encode() + b" Td " + _pdf_literal_bytes(header[:70]) + b" Tj " + f"{-margin_left:.0f} {-header_y:.0f}".encode() + b" Td")
        for text, size, x, line_y, font in page_lines:
            if text == "":
                continue
            font_name = {"B": b"/F2", "I": b"/F3"}.get(font, b"/F1")
            stream_parts.append(font_name + b" " + str(size).encode() + b" Tf " + f"{x:.0f} {line_y:.0f}".encode() + b" Td " + _pdf_literal_bytes(text) + b" Tj " + f"{-(x):.0f} {-(line_y):.0f}".encode() + b" Td")
        if page.get("show_number"):
            number = page.get("number") or i + 1
            number_text = str(number)
            number_x = (width / 2) - (len(number_text) * 2.25)
            stream_parts.append(b"/F1 9 Tf " + f"{number_x:.0f} {footer_y:.0f}".encode() + b" Td " + _pdf_literal_bytes(number_text) + b" Tj")
        stream_parts.append(b"ET")
        content = b"\n".join(stream_parts)
        resources = b"<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >> /F2 << /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >> /F3 << /Type /Font /Subtype /Type1 /BaseFont /Times-Italic /Encoding /WinAnsiEncoding >> >> >>"
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources ".encode() + resources + f" /Contents {content_obj} 0 R >>".encode())
        objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
    info_obj_num = len(objects) + 1
    info_parts = [
        f"/Title ({_pdf_escape(project.title)})",
        f"/Author ({_pdf_escape(project.author)})",
        f"/Subject ({_pdf_escape(project.subtitle or project.title)})",
        f"/Lang ({_pdf_escape(project.language)})",
    ]
    if project.publisher:
        info_parts.append(f"/Publisher ({_pdf_escape(project.publisher)})")
    if project.copyright_year:
        info_parts.append(f"/Rights ({_pdf_escape(_copyright_notice(project))})")
    objects.append(("<< " + " ".join(info_parts) + " >>").encode("cp1252", errors="replace"))

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for objnum, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{objnum} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(f"trailer << /Size {len(objects)+1} /Root 1 0 R /Info {info_obj_num} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


@router.post("/organizer/review-structure")
def review_structure_for_organizer(
    payload: OrganizerStructureEditRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:update_self")),
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_TEXT_BOOK_ORGANIZER:
        raise HTTPException(status_code=404, detail="Not found.")

    document = (
        db.query(BookOrganizerDocument)
        .filter(BookOrganizerDocument.id == payload.document_id, BookOrganizerDocument.user_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    plan = (
        db.query(BookOrganizationPlan)
        .filter(BookOrganizationPlan.id == payload.plan_id, BookOrganizationPlan.document_id == document.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    blocks = (
        db.query(BookOrganizerBlock)
        .filter(BookOrganizerBlock.document_id == document.id)
        .order_by(BookOrganizerBlock.block_index.asc())
        .all()
    )
    block_map = {block.block_id: block for block in blocks}

    chapters = [
        {
            "chapter_index": int(chapter.get("chapter_index", index + 1)),
            "chapter_title": chapter.get("chapter_title") or f"Chapter {index + 1}",
            "marker": chapter.get("marker"),
            "title": chapter.get("title"),
            "type": chapter.get("type", "chapter"),
            "warnings": chapter.get("warnings", []),
            "block_ids": list(chapter.get("block_ids", [])),
        }
        for index, chapter in enumerate(plan.structure.get("chapters", []))
    ]
    _validate_plan_block_ids(chapters, block_map)

    merge_targets = sorted(set(payload.merge_chapter_indexes))
    if any(index < 1 for index in merge_targets):
        raise HTTPException(status_code=422, detail="merge_chapter_indexes must be >= 1")
    for merge_index in reversed(merge_targets):
        if merge_index >= len(chapters):
            raise HTTPException(status_code=422, detail=f"Cannot merge chapter {merge_index} with next chapter.")
        chapters[merge_index - 1]["block_ids"].extend(chapters[merge_index]["block_ids"])
        del chapters[merge_index]

    for split in payload.split_operations:
        chapter_index = int(split.get("chapter_index", 0))
        boundary_block_id = (split.get("boundary_block_id") or "").strip()
        if chapter_index < 1 or chapter_index > len(chapters):
            raise HTTPException(status_code=422, detail="Invalid chapter_index for split.")
        if not boundary_block_id:
            raise HTTPException(status_code=422, detail="boundary_block_id is required for split.")

        target = chapters[chapter_index - 1]
        block_ids = target["block_ids"]
        if boundary_block_id not in block_ids:
            raise HTTPException(status_code=422, detail={"invalid_block_ids": [boundary_block_id]})
        split_at = block_ids.index(boundary_block_id)
        if split_at <= 0:
            raise HTTPException(status_code=422, detail="Split boundary must not be the first block in chapter.")

        target["block_ids"] = block_ids[:split_at]
        chapters.insert(
            chapter_index,
            {
                "chapter_index": chapter_index + 1,
                "chapter_title": f"{target['chapter_title']} (Part 2)",
                "type": target.get("type", "chapter"),
                "warnings": [],
                "block_ids": block_ids[split_at:],
            },
        )

    for index, chapter in enumerate(chapters, start=1):
        chapter["chapter_index"] = index
        if index in payload.chapter_title_overrides:
            chapter["chapter_title"] = (payload.chapter_title_overrides[index] or "").strip() or chapter["chapter_title"]

    _validate_plan_block_ids(chapters, block_map)

    structure = {
        "title_candidate": plan.structure.get("title_candidate") or document.title or "Untitled",
        "chapters": chapters,
        "chapter_count": len(chapters),
        "detection_mode": plan.structure.get("detection_mode"),
        "requires_review": False,
        "review_status": "approved",
        "approved": True,
        "warnings": [*plan.structure.get("warnings", []), *_book_organizer_structure_warnings(len(chapters))],
    }
    new_plan = BookOrganizationPlan(
        document_id=document.id,
        name=payload.plan_name.strip() or "Edited plan",
        structure=structure,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"plan_id": new_plan.id, "document_id": document.id, "structure": structure}


@router.post("/organizer/preview")
def preview_organization(
    payload: OrganizerPreviewRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:read_self")),
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_TEXT_BOOK_ORGANIZER:
        raise HTTPException(status_code=404, detail="Not found.")

    document = (
        db.query(BookOrganizerDocument)
        .filter(BookOrganizerDocument.id == payload.document_id, BookOrganizerDocument.user_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    plan = (
        db.query(BookOrganizationPlan)
        .filter(BookOrganizationPlan.id == payload.plan_id, BookOrganizationPlan.document_id == document.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    blocks = (
        db.query(BookOrganizerBlock)
        .filter(BookOrganizerBlock.document_id == document.id)
        .order_by(BookOrganizerBlock.block_index.asc())
        .all()
    )
    block_map = {block.block_id: block for block in blocks}

    chapters = _build_organizer_chapters_from_plan(plan, block_map)

    chapter_titles = [chapter.get("chapter_title") for chapter in chapters]
    return {
        "document_id": document.id,
        "plan_id": plan.id,
        "detected_chapter_count": len(chapters),
        "chapter_titles": chapter_titles,
        "warnings": plan.structure.get("warnings", []),
        "requires_review": bool(plan.structure.get("requires_review", False)),
        "review_status": plan.structure.get("review_status", "pending"),
        "approved": bool(plan.structure.get("approved") or plan.structure.get("review_status") == "approved"),
        "detection_mode": plan.structure.get("detection_mode"),
        "chapters": chapters,
    }


@router.post("/organizer/export-txt")
def export_organization_txt(
    payload: OrganizerExportRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:export_self")),
    db: Session = Depends(get_db),
):
    document, plan, project = _resolve_organizer_export_project(payload=payload, user=user, db=db)
    _log_organizer_export(document=document, plan=plan, project=project, export_format="txt")
    safe_title = _safe_export_basename(project.title or document.title)
    return PlainTextResponse(
        content=_canonical_plaintext(project),
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.txt"'},
        media_type="text/plain; charset=utf-8",
    )


@router.post("/organizer/export-markdown")
def export_organization_markdown(
    payload: OrganizerExportRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:export_self")),
    db: Session = Depends(get_db),
):
    document, plan, project = _resolve_organizer_export_project(payload=payload, user=user, db=db)
    _log_organizer_export(document=document, plan=plan, project=project, export_format="markdown")
    safe_title = _safe_export_basename(project.title or document.title)
    return PlainTextResponse(
        content=_canonical_markdown(project),
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.md"'},
        media_type="text/markdown; charset=utf-8",
    )


@router.post("/organizer/export-docx")
def export_organization_docx(
    payload: OrganizerExportRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:export_self")),
    db: Session = Depends(get_db),
):
    document, plan, project = _resolve_organizer_export_project(payload=payload, user=user, db=db)
    _log_organizer_export(document=document, plan=plan, project=project, export_format="docx")
    export = BookExport(
        filename=f"{_safe_export_basename(project.title or document.title)}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        payload=_build_docx_export(project),
    )
    return Response(content=export.payload, media_type=export.media_type, headers={"Content-Disposition": f'attachment; filename="{export.filename}"'})


@router.post("/organizer/export-epub")
def export_organization_epub(
    payload: OrganizerExportRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:export_self")),
    db: Session = Depends(get_db),
):
    document, plan, project = _resolve_organizer_export_project(payload=payload, user=user, db=db)
    _log_organizer_export(document=document, plan=plan, project=project, export_format="epub")
    export = BookExport(
        filename=f"{_safe_export_basename(project.title or document.title)}.epub",
        media_type="application/epub+zip",
        payload=_build_epub_export(project),
    )
    return Response(content=export.payload, media_type=export.media_type, headers={"Content-Disposition": f'attachment; filename="{export.filename}"'})


@router.post("/organizer/export-print-pdf")
def export_organization_print_pdf(
    payload: OrganizerExportRequest,
    request: Request,
    user: User = Depends(require_permission("book_organizer:export_self")),
    db: Session = Depends(get_db),
):
    document, plan, project = _resolve_organizer_export_project(payload=payload, user=user, db=db)
    _log_organizer_export(document=document, plan=plan, project=project, export_format="print_pdf")
    export = BookExport(
        filename=f"{_safe_export_basename(project.title or document.title)}-print-interior.pdf",
        media_type="application/pdf",
        payload=_build_pdf_export(project, trim_size=payload.trim_size, chapter_start=payload.chapter_start),
    )
    return Response(content=export.payload, media_type=export.media_type, headers={"Content-Disposition": f'attachment; filename="{export.filename}"'})


@router.get("")
def list_audiobooks(request: Request, response: Response, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
    response.headers["x-audiobook-auth-mode"] = _auth_mode(user, used_guest)
    books = db.query(Audiobook).filter(Audiobook.user_id == user.id).order_by(Audiobook.created_at.desc()).all()
    return {"items": [_serialize_audiobook(book) for book in books], "auth_mode": response.headers["x-audiobook-auth-mode"]}


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

    if book.status in {"pending", "generating_chapters"}:
        return {"ok": True, "status": book.status, "audiobook": _serialize_audiobook(book)}

    book.status = "pending"
    db.commit()
    _start_background_generation(audiobook_id=book.id, user_id=user.id, base_url=str(request.base_url))
    db.refresh(book)
    return {"ok": True, "status": book.status, "audiobook": _serialize_audiobook(book)}


@router.get("/{audiobook_id}/generation-status")
def get_generation_status(audiobook_id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")
    return {"audiobook_id": audiobook_id, "generation_progress": _build_generation_progress(book)}


@router.post("/{audiobook_id}/chapters/{chapter_index}/generate")
def generate_single_chapter(audiobook_id: int, chapter_index: int, request: Request, regenerate: bool = False, db: Session = Depends(get_db)):
    user, _ = _resolve_audiobook_user(request, db)
    book = db.query(Audiobook).filter(Audiobook.id == audiobook_id, Audiobook.user_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Audiobook not found.")
    chapter = db.query(AudiobookChapter).filter(AudiobookChapter.audiobook_id == audiobook_id, AudiobookChapter.chapter_index == chapter_index).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found.")

    saved_asset = None
    if chapter.audio_asset_id:
        saved_asset = db.query(AudioAsset).filter(AudioAsset.id == chapter.audio_asset_id, AudioAsset.voice == book.voice).first()
    if not saved_asset:
        saved_asset = db.query(AudioAsset).filter(AudioAsset.text_hash == chapter.text_hash, AudioAsset.voice == book.voice).first()

    if saved_asset and not regenerate:
        chapter.audio_asset_id = saved_asset.id
        chapter.audio_url = saved_asset.audio_url
        chapter.status = "completed"
        _hydrate_audio_asset(saved_asset, book, chapter)
        db.commit()
        return {
            "ok": True,
            "chapter_index": chapter_index,
            "status": chapter.status,
            "audio_url": chapter.audio_url,
            "audio": _serialize_audio_asset(saved_asset, book, chapter),
            "provider_called": False,
            "message": "Saved audio already exists. Use saved audio or regenerate?",
            "default_action": "use_saved_audio",
        }

    if chapter.audio_url and not regenerate:
        chapter.status = "completed"
        db.commit()
        return {"ok": True, "chapter_index": chapter_index, "status": chapter.status, "audio_url": chapter.audio_url, "provider_called": False}

    chapter.status = "generating"
    db.commit()
    try:
        audio_url, cached = generate_tts_audio_url(request=None, text=chapter.text, voice=book.voice, base_url=str(request.base_url), force=regenerate)
        asset = saved_asset or db.query(AudioAsset).filter(AudioAsset.text_hash == chapter.text_hash, AudioAsset.voice == book.voice).first()
        if not asset:
            asset = AudioAsset(text_hash=chapter.text_hash, voice=book.voice, audio_url=audio_url)
            db.add(asset)
            db.flush()
        asset.audio_url = audio_url
        _hydrate_audio_asset(asset, book, chapter)
        chapter.audio_asset_id = asset.id
        chapter.audio_url = audio_url
        chapter.status = "completed"
        db.commit()
        return {
            "ok": True,
            "chapter_index": chapter_index,
            "status": chapter.status,
            "audio_url": chapter.audio_url,
            "audio": _serialize_audio_asset(asset, book, chapter),
            "provider_called": not cached,
            "regenerated": regenerate,
        }
    except Exception as exc:
        chapter.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Chapter generation failed: {exc}") from exc


@router.post("/{audiobook_id}/progress")
def update_progress(audiobook_id: int, payload: ProgressUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
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
    return {"ok": True, "auth_mode": _auth_mode(user, used_guest)}


@router.get("/{audiobook_id}/reflections")
def list_reflections(audiobook_id: int, request: Request, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
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
        ],
        "auth_mode": _auth_mode(user, used_guest),
    }


@router.put("/{audiobook_id}/chapters/{chapter_index}/reflection")
def save_reflection(audiobook_id: int, chapter_index: int, payload: ReflectionRequest, request: Request, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
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
    return {"ok": True, "chapter_index": chapter_index, "prompt": prompt, "auth_mode": _auth_mode(user, used_guest)}


@router.post("/{audiobook_id}/reflections/summary")
def summarize_reflections(audiobook_id: int, payload: ReflectionSummaryRequest, request: Request, db: Session = Depends(get_db)):
    user, used_guest = _resolve_audiobook_user(request, db)
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
    return {"summary": summary, "count": len(reflections), "auth_mode": _auth_mode(user, used_guest)}
