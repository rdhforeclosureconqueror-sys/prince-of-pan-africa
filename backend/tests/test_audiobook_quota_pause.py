import os
from pathlib import Path
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/test_audiobook_quota_pause.db")
os.environ.setdefault("SESSION_SECRET", "test-session-secret")
os.environ.setdefault("ENVIRONMENT", "test")

from app.database import Base, SessionLocal, engine
from app.models import Audiobook, AudiobookChapter, User, compute_text_checksum
from app.routes import audiobook, chat


def setup_module():
    db_file = Path("/tmp/test_audiobook_quota_pause.db")
    if db_file.exists():
        db_file.unlink()
    Base.metadata.create_all(bind=engine)


def _reset_db():
    with SessionLocal() as db:
        db.query(AudiobookChapter).delete()
        db.query(Audiobook).delete()
        db.query(User).delete()
        db.commit()


def _book_with_chapters():
    _reset_db()
    with SessionLocal() as db:
        user = User(email="quota@example.com", password_hash="x", role="member")
        db.add(user)
        db.flush()
        book = Audiobook(
            user_id=user.id,
            title="Quota Book",
            author="A",
            voice="alloy",
            source_type="text",
            status="pending",
            chapter_count=3,
            total_characters=30,
        )
        db.add(book)
        db.flush()
        for idx in range(1, 4):
            text = f"Chapter {idx} text"
            db.add(AudiobookChapter(
                audiobook_id=book.id,
                chapter_index=idx,
                title=f"Chapter {idx}",
                text=text,
                text_hash=compute_text_checksum(text),
                character_count=len(text),
                status="queued",
            ))
        db.commit()
        return user.id, book.id


def test_wrapped_500_quota_body_classified_as_provider_quota_exceeded():
    body = '{"error":"Error code: 429 - You exceeded your current quota. Please check your plan and billing details."}'
    classified = chat.classify_tts_provider_error(500, body)
    assert classified["error_type"] == "provider_quota_exceeded"
    assert classified["retryable"] is True


def test_rate_limit_body_classified_as_provider_rate_limited():
    classified = chat.classify_tts_provider_error(500, "upstream 429 Too Many Requests rate limit reached")
    assert classified["error_type"] == "provider_rate_limited"
    assert classified["retryable"] is True


def test_quota_error_pauses_job_and_keeps_completed_chapters_retryable(monkeypatch):
    user_id, book_id = _book_with_chapters()
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs["text"])
        if len(calls) == 1:
            return "http://testserver/static/audio/one.mp3", False
        raise HTTPException(status_code=500, detail={
            "reason": "Error code: 429 - You exceeded your current quota. Please check your plan and billing details.",
            "provider_status": 500,
            "provider_body_snippet": "Error code: 429 - You exceeded your current quota. Please check your plan and billing details.",
        })

    monkeypatch.setattr(audiobook, "generate_tts_audio_url", fake_generate)
    audiobook._generate_audio_for_book_job(audiobook_id=book_id, user_id=user_id, base_url="http://testserver/")

    with SessionLocal() as db:
        book = db.query(Audiobook).get(book_id)
        chapters = sorted(book.chapters, key=lambda c: c.chapter_index)
        progress = audiobook._build_generation_progress(book)
        assert book.status == "needs_retry"
        assert chapters[0].status == "completed"
        assert chapters[1].status == "failed"
        assert chapters[2].status == "queued"
        assert progress["completed_chapters"] == 1
        assert progress["failed_chapters"] == 1
        assert progress["pending_chapters"] == 2
        assert progress["paused_reason"] == "provider_quota_exceeded"
        assert progress["last_error_type"] == "provider_quota_exceeded"
        assert progress["retryable"] is True
        assert progress["user_message"] == chat.TTS_PROVIDER_LIMIT_MESSAGE


def test_resume_skips_completed_chapters(monkeypatch):
    user_id, book_id = _book_with_chapters()
    with SessionLocal() as db:
        chapter = db.query(AudiobookChapter).filter_by(audiobook_id=book_id, chapter_index=1).one()
        chapter.status = "completed"
        chapter.audio_url = "http://testserver/static/audio/already.mp3"
        db.commit()

    generated = []
    def fake_generate(**kwargs):
        generated.append(kwargs["text"])
        return f"http://testserver/static/audio/{len(generated)}.mp3", False

    monkeypatch.setattr(audiobook, "generate_tts_audio_url", fake_generate)
    audiobook._generate_audio_for_book_job(audiobook_id=book_id, user_id=user_id, base_url="http://testserver/")

    assert generated == ["Chapter 2 text", "Chapter 3 text"]
    with SessionLocal() as db:
        book = db.query(Audiobook).get(book_id)
        assert book.status == "complete"
        assert audiobook._build_generation_progress(book)["completed_chapters"] == 3


def test_user_facing_quota_message_is_clear():
    assert chat.TTS_PROVIDER_LIMIT_MESSAGE == (
        "Audiobook generation paused because the text-to-speech provider reached its usage limit. "
        "Completed chapters were saved. You can resume after quota/billing is restored."
    )
