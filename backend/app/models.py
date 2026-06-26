from datetime import datetime
import hashlib

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event, inspect
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

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
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    users: Mapped[list["UserRole"]] = relationship(back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    roles: Mapped[list[Role]] = relationship(secondary="role_permissions", back_populates="permissions")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="users")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)



class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tier: Mapped[str] = mapped_column(String(64), nullable=False, default="community_member")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    user: Mapped[User | None] = relationship(back_populates="subscriptions")


class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


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


class GarveySyncEvent(Base):
    __tablename__ = "garvey_sync_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    external_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class AudioAsset(Base):
    __tablename__ = "audio_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    voice: Mapped[str] = mapped_column(String(64), nullable=False, default="alloy")
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    audiobook_id: Mapped[int | None] = mapped_column(ForeignKey("audiobooks.id"), nullable=True, index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("audiobook_chapters.id"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False, default="mp3")
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_image_path: Mapped[str] = mapped_column(Text, nullable=False, default="/book-covers/library-placeholder.svg")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    voice: Mapped[str] = mapped_column(String(64), nullable=False, default="alloy")
    access_level: Mapped[str] = mapped_column(String(32), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total_characters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

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


class ContentShare(Base):
    __tablename__ = "content_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    share_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    visitor_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visitor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    registration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    membership_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class BookOrganizerDocument(Base):
    __tablename__ = "book_organizer_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "source_text_hash", name="uq_organizer_user_source_hash"),)

    blocks: Mapped[list["BookOrganizerBlock"]] = relationship(back_populates="document")
    plans: Mapped[list["BookOrganizationPlan"]] = relationship(back_populates="document")


class BookOrganizerBlock(Base):
    __tablename__ = "book_organizer_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("book_organizer_documents.id"), nullable=False, index=True)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    block_id: Mapped[str] = mapped_column(String(80), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "block_index", name="uq_organizer_document_block_index"),
        UniqueConstraint("document_id", "block_id", name="uq_organizer_document_block_id"),
    )

    document: Mapped[BookOrganizerDocument] = relationship(back_populates="blocks")


class BookOrganizationPlan(Base):
    __tablename__ = "book_organization_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("book_organizer_documents.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default plan")
    structure: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped[BookOrganizerDocument] = relationship(back_populates="plans")


def compute_text_checksum(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


@event.listens_for(BookOrganizerBlock, "before_insert")
def _set_block_checksum_before_insert(mapper, connection, target):
    target.checksum = compute_text_checksum(target.text)


@event.listens_for(Session, "before_flush")
def _enforce_immutable_book_organizer_blocks(session, flush_context, instances):
    for obj in session.dirty:
        if not isinstance(obj, BookOrganizerBlock):
            continue

        state = inspect(obj)
        text_history = state.attrs.text.history
        checksum_history = state.attrs.checksum.history

        if text_history.has_changes() or checksum_history.has_changes():
            raise ValueError("Book organizer block text and checksum are immutable once created.")

class GuestSession(Base):
    __tablename__ = "guest_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    merged_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ActivityType(Base):
    __tablename__ = "activity_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    default_star: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    activity_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_module: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    participation_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    star_award: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class ParticipationPoint(Base):
    __tablename__ = "participation_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class StarTransaction(Base):
    __tablename__ = "star_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False, default="earn")
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    streak_type: Mapped[str] = mapped_column(String(64), nullable=False, default="daily")
    current_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ActivityHistory(Base):
    __tablename__ = "activity_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    verified_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RewardEvent(Base):
    __tablename__ = "reward_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    reward_type: Mapped[str] = mapped_column(String(128), nullable=False)
    star_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="issued")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ActivityAuditLog(Base):
    __tablename__ = "activity_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id"), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    before: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    after: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CommunityReputation(Base):
    __tablename__ = "community_reputation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)
    verified_contributions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verifications_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_accuracy: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    trust_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leadership_level: Mapped[str] = mapped_column(String(64), nullable=False, default="Emerging Steward")
    consistency_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
class PreparednessHouseholdProfile(Base):
    __tablename__ = "preparedness_household_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)
    household_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    neighborhood: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    water_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    food_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medical_status: Mapped[str] = mapped_column(String(64), nullable=False, default="getting_started")
    power_status: Mapped[str] = mapped_column(String(64), nullable=False, default="getting_started")
    communication_status: Mapped[str] = mapped_column(String(64), nullable=False, default="getting_started")
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class PreparednessInventoryItem(Base):
    __tablename__ = "preparedness_inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general", index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(64), nullable=False, default="units")
    target_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class PreparednessVolunteer(Base):
    __tablename__ = "preparedness_volunteers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="neighbor_support", index=True)
    availability: Mapped[str] = mapped_column(String(64), nullable=False, default="as_available")
    neighborhood: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class MutualAidFund(Base):
    __tablename__ = "mutual_aid_funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(128), nullable=False, default="Building Toward Activation")
    activation_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=20000)
    current_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserve_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    approval_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class MutualAidContribution(Base):
    __tablename__ = "mutual_aid_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_funds.id"), nullable=False, index=True)
    contributor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="recorded")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidRequest(Base):
    __tablename__ = "mutual_aid_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_funds.id"), nullable=False, index=True)
    requester_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(128), nullable=False, default="unclassified")
    amount_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    narrative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    urgency: Mapped[str] = mapped_column(String(64), nullable=False, default="standard")
    preferred_support_method: Mapped[str] = mapped_column(String(128), nullable=False, default="community_follow_up")
    policy_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class MutualAidRequestDocument(Base):
    __tablename__ = "mutual_aid_request_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(128), nullable=False, default="supporting")
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidReview(Base):
    __tablename__ = "mutual_aid_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    reviewer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidDecision(Base):
    __tablename__ = "mutual_aid_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    decided_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    amount_approved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    appeal_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    appeal_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    appeal_instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidDisbursement(Base):
    __tablename__ = "mutual_aid_disbursements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    recipient_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    receipt_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidDisbursementStatusHistory(Base):
    __tablename__ = "mutual_aid_disbursement_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    disbursement_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_disbursements.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidPolicyVersion(Base):
    __tablename__ = "mutual_aid_policy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effective_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidMemberAcceptance(Base):
    __tablename__ = "mutual_aid_member_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    policy_version_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_policy_versions.id"), nullable=False, index=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidAuditLog(Base):
    __tablename__ = "mutual_aid_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    before: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    after: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidRequestStatusHistory(Base):
    __tablename__ = "mutual_aid_request_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidCommitteeMember(Base):
    __tablename__ = "mutual_aid_committee_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(128), nullable=False, default="reviewer")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="inactive")
    appointed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidConflictDisclosure(Base):
    __tablename__ = "mutual_aid_conflict_disclosures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=True, index=True)
    committee_member_id: Mapped[int | None] = mapped_column(ForeignKey("mutual_aid_committee_members.id"), nullable=True, index=True)
    disclosure: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidAppeal(Base):
    __tablename__ = "mutual_aid_appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=False, index=True)
    appellant_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidFraudReview(Base):
    __tablename__ = "mutual_aid_fraud_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("mutual_aid_requests.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    risk_level: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidReconciliationReport(Base):
    __tablename__ = "mutual_aid_reconciliation_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_funds.id"), nullable=False, index=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    totals: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidCategoryBudget(Base):
    __tablename__ = "mutual_aid_category_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_aid_funds.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    budget_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MutualAidVendorRecipient(Base):
    __tablename__ = "mutual_aid_vendor_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="inactive")
    contact_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
