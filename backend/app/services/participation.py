from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import (
    Activity,
    ActivityAuditLog,
    ActivityHistory,
    ActivityType,
    GuestSession,
    ParticipationPoint,
    StarTransaction,
    User,
    VerificationRecord,
)

DEFAULT_ACTIVITY_TYPES = {
    "book_read": {"points": 10, "star": 10},
    "audiobook_listen": {"points": 8, "star": 8},
    "language_lesson": {"points": 7, "star": 7},
    "brain_game_played": {"points": 6, "star": 6},
    "content_shared": {"points": 4, "star": 4},
    "daily_history_read": {"points": 3, "star": 3},
    "word_of_day_viewed": {"points": 3, "star": 3},
    "volunteer_task_completed": {"points": 15, "star": 15},
    "event_attended": {"points": 12, "star": 12},
    "community_help": {"points": 12, "star": 12},
    "community_onboarding_completed": {"points": 20, "star": 20},
    "builder_onboarding_completed": {"points": 20, "star": 20},
}


def get_or_create_guest_session(db: Session, guest_session_id: str | None = None) -> GuestSession:
    token = (guest_session_id or "").strip() or f"guest_{uuid4().hex}"
    guest = db.query(GuestSession).filter(GuestSession.session_id == token).first()
    if not guest:
        guest = GuestSession(session_id=token, expires_at=datetime.utcnow() + timedelta(days=30))
        db.add(guest)
        db.flush()
    return guest


def get_activity_type(db: Session, name: str) -> ActivityType:
    normalized = (name or "general_participation").strip().lower().replace(" ", "_")
    defaults = DEFAULT_ACTIVITY_TYPES.get(normalized, {"points": 5, "star": 5})
    activity_type = db.query(ActivityType).filter(ActivityType.name == normalized).first()
    if not activity_type:
        activity_type = ActivityType(
            name=normalized,
            description=f"Participation submitted for {normalized.replace('_', ' ')}.",
            default_points=defaults["points"],
            default_star=defaults["star"],
            verification_required=False,
            active=True,
        )
        db.add(activity_type)
        db.flush()
    return activity_type


def submit_activity(
    db: Session,
    *,
    user: User | None,
    guest_session_id: str | None,
    activity_type_name: str,
    source_module: str,
    metadata: dict | None = None,
) -> Activity:
    if not user and not guest_session_id:
        guest = get_or_create_guest_session(db)
    elif not user:
        guest = get_or_create_guest_session(db, guest_session_id)
    else:
        guest = get_or_create_guest_session(db, guest_session_id) if guest_session_id else None

    activity_type = get_activity_type(db, activity_type_name)
    verification_status = "pending" if activity_type.verification_required else "verified"
    points = activity_type.default_points
    star = activity_type.default_star if verification_status == "verified" else 0

    activity = Activity(
        user_id=user.id if user else None,
        guest_session_id=guest.session_id if guest else None,
        activity_type=activity_type.name,
        source_module=(source_module or "community").strip().lower(),
        verification_status=verification_status,
        participation_points=points,
        star_award=star,
        metadata_=metadata or {},
    )
    db.add(activity)
    db.flush()

    db.add(VerificationRecord(activity_id=activity.id, status=verification_status, notes="Auto-verified by Phase 1 participation engine."))
    db.add(ParticipationPoint(activity_id=activity.id, user_id=activity.user_id, guest_session_id=activity.guest_session_id, points=points, reason=activity.activity_type))
    if star:
        db.add(StarTransaction(activity_id=activity.id, user_id=activity.user_id, guest_session_id=activity.guest_session_id, amount=star, transaction_type="earn", reason=activity.activity_type))
    db.add(ActivityHistory(activity_id=activity.id, user_id=activity.user_id, guest_session_id=activity.guest_session_id, event_type="activity_submitted", description=f"{activity.activity_type} submitted through {activity.source_module}."))
    db.add(ActivityAuditLog(activity_id=activity.id, actor_user_id=activity.user_id, action="participation_engine_award", before={}, after={"points": points, "star": star, "verification_status": verification_status}))
    return activity


def participation_summary(db: Session, user_id: int | None = None, guest_session_id: str | None = None) -> dict:
    query = db.query(Activity)
    if user_id is not None:
        query = query.filter(Activity.user_id == user_id)
    elif guest_session_id:
        query = query.filter(Activity.guest_session_id == guest_session_id)
    else:
        return {"activity_count": 0, "participation_score": 0, "star": 0, "current_rank": "Guest"}

    activities = query.all()
    score = sum(item.participation_points or 0 for item in activities)
    star = sum(item.star_award or 0 for item in activities)
    rank = "Guest"
    if user_id is not None:
        rank = "Community Leader" if star >= 500 else "Steward" if star >= 250 else "Contributor" if star >= 100 else "Community Member" if star >= 25 else "Registered User"
    return {"activity_count": len(activities), "participation_score": score, "star": star, "current_rank": rank}


def merge_guest_participation(db: Session, *, guest_session_id: str, user: User) -> int:
    guest = db.query(GuestSession).filter(GuestSession.session_id == guest_session_id).first()
    if not guest:
        return 0
    activities = db.query(Activity).filter(Activity.guest_session_id == guest.session_id, Activity.user_id.is_(None)).all()
    for activity in activities:
        activity.user_id = user.id
    db.query(ParticipationPoint).filter(ParticipationPoint.guest_session_id == guest.session_id, ParticipationPoint.user_id.is_(None)).update({"user_id": user.id}, synchronize_session=False)
    db.query(StarTransaction).filter(StarTransaction.guest_session_id == guest.session_id, StarTransaction.user_id.is_(None)).update({"user_id": user.id}, synchronize_session=False)
    db.query(ActivityHistory).filter(ActivityHistory.guest_session_id == guest.session_id, ActivityHistory.user_id.is_(None)).update({"user_id": user.id}, synchronize_session=False)
    guest.merged_user_id = user.id
    guest.merged_at = datetime.utcnow()
    return len(activities)
