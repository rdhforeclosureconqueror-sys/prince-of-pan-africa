from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    profile: Mapped["MemberProfile | None"] = relationship(back_populates="user", uselist=False)
    activities: Mapped[list["ActivityLog"]] = relationship(back_populates="user")
    assessments: Mapped[list["LeadershipAssessment"]] = relationship(back_populates="user")
    audiobooks: Mapped[list["Audiobook"]] = relationship(back_populates="user")
    chapter_reflections: Mapped[list["AudiobookChapterReflection"]] = relationship(back_populates="user")


class MemberProfile(Base):
    __tablename__ = "member_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="member")
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="activities")


class LeadershipAssessment(Base):
    __tablename__ = "leadership_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    child_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    submission_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    responses: Mapped[str] = mapped_column(Text, nullable=False)
    scores: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="assessments")


class AudioAsset(Base):
    __tablename__ = "audio_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    voice: Mapped[str] = mapped_column(String(64), nullable=False, default="alloy")
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("text_hash", "voice", name="uq_audio_asset_hash_voice"),)


class Audiobook(Base):
    __tablename__ = "audiobooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="paste")
    source_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    voice: Mapped[str] = mapped_column(String(64), nullable=False, default="alloy")
    access_level: Mapped[str] = mapped_column(String(32), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total_characters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "content_hash", "voice", name="uq_user_content_voice"),)

    user: Mapped[User] = relationship(back_populates="audiobooks")
    chapters: Mapped[list["AudiobookChapter"]] = relationship(back_populates="audiobook")
    progress: Mapped[list["AudiobookProgress"]] = relationship(back_populates="audiobook")
    reflections: Mapped[list["AudiobookChapterReflection"]] = relationship(back_populates="audiobook")


class AudiobookChapter(Base):
    __tablename__ = "audiobook_chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audiobook_id: Mapped[int] = mapped_column(ForeignKey("audiobooks.id"), nullable=False, index=True)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_asset_id: Mapped[int | None] = mapped_column(ForeignKey("audio_assets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("audiobook_id", "chapter_index", name="uq_audiobook_chapter_index"),)

    audiobook: Mapped[Audiobook] = relationship(back_populates="chapters")


class AudiobookProgress(Base):
    __tablename__ = "audiobook_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audiobook_id: Mapped[int] = mapped_column(ForeignKey("audiobooks.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    playback_rate: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    completed_chapters: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("audiobook_id", "user_id", name="uq_audiobook_user_progress"),)

    audiobook: Mapped[Audiobook] = relationship(back_populates="progress")


class AudiobookChapterReflection(Base):
    __tablename__ = "audiobook_chapter_reflections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audiobook_id: Mapped[int] = mapped_column(ForeignKey("audiobooks.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("audiobook_id", "user_id", "chapter_index", name="uq_reflection_scope"),)

    audiobook: Mapped[Audiobook] = relationship(back_populates="reflections")
    user: Mapped[User] = relationship(back_populates="chapter_reflections")
