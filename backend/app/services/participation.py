from __future__ import annotations

from datetime import datetime, timedelta
import logging
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    ActivityAuditLog,
    ActivityHistory,
    ActivityType,
    CommunityReputation,
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
    "language_match_completed": {"points": 5, "star": 5},
    "swahili_lesson_completed": {"points": 7, "star": 7},
    "yoruba_lesson_completed": {"points": 7, "star": 7},
    "quiz_completed": {"points": 5, "star": 5},
    "chapter_read": {"points": 10, "star": 10},
    "decolonization_lesson_completed": {"points": 9, "star": 9},
    "member_referred": {"points": 20, "star": 20},
    "brain_game_played": {"points": 6, "star": 6},
    "content_shared": {"points": 4, "star": 4},
    "daily_history_read": {"points": 3, "star": 3},
    "word_of_day_viewed": {"points": 3, "star": 3},
    "volunteer_task_completed": {"points": 15, "star": 15},
    "event_attended": {"points": 12, "star": 12},
    "community_help": {"points": 12, "star": 12},
    "community_onboarding_completed": {"points": 20, "star": 20},
    "builder_onboarding_completed": {"points": 20, "star": 20},
    "share_verified": {"points": 12, "star": 12},
    "community_verification": {"points": 3, "star": 3},
}

LABOR_CATEGORIES = {
    "learning": "Learning Labor",
    "community": "Community Labor",
    "growth": "Growth Labor",
    "builder": "Builder Labor",
}

VERIFICATIONS_REQUIRED = 3
FIRST_VERIFIER_STAR = 3
FOLLOWUP_VERIFIER_STAR = 1

RANK_THRESHOLDS = [
    (0, "Registered User"),
    (25, "Community Member"),
    (100, "Contributor"),
    (250, "Steward"),
    (500, "Community Leader"),
]

STAR_OPPORTUNITIES = [
    {"activity_type": "chapter_read", "source_module": "books", "title": "Read a chapter", "star": 10, "href": "/library"},
    {"activity_type": "audiobook_listen", "source_module": "audiobooks", "title": "Listen to an audiobook", "star": 8, "href": "/study"},
    {"activity_type": "swahili_lesson_completed", "source_module": "swahili", "title": "Complete a Swahili lesson", "star": 7, "href": "/languages"},
    {"activity_type": "yoruba_lesson_completed", "source_module": "yoruba", "title": "Complete a Yoruba lesson", "star": 7, "href": "/languages"},
    {"activity_type": "brain_game_played", "source_module": "brain_games", "title": "Finish a brain game", "star": 6, "href": "/brain-training"},
    {"activity_type": "quiz_completed", "source_module": "learning", "title": "Complete a quiz", "star": 5, "href": "/portal/decolonize"},
    {"activity_type": "content_shared", "source_module": "community", "title": "Share community content", "star": 4, "href": "#community-feed"},
    {"activity_type": "event_attended", "source_module": "events", "title": "Attend an event", "star": 12, "href": "/calendar"},
    {"activity_type": "member_referred", "source_module": "referrals", "title": "Refer a member", "star": 20, "href": "/membership"},
]

logger = logging.getLogger("simba.participation")



TRUST_LADDER = [
    {"level": "Community Member", "threshold": 0},
    {"level": "Verified Contributor", "threshold": 25},
    {"level": "Community Builder", "threshold": 75},
    {"level": "Community Steward", "threshold": 150},
    {"level": "Community Leader", "threshold": 300},
]


def trust_ladder_progress(trust_score: int) -> dict:
    current = TRUST_LADDER[0]
    next_level = None
    for idx, level in enumerate(TRUST_LADDER):
        if trust_score >= level["threshold"]:
            current = level
            next_level = TRUST_LADDER[idx + 1] if idx + 1 < len(TRUST_LADDER) else None
    if not next_level:
        return {"current_level": current["level"], "next_level": "Highest community level", "percent": 100, "trust_to_next_level": 0, "levels": TRUST_LADDER}
    span = max(next_level["threshold"] - current["threshold"], 1)
    percent = min(100, round(((trust_score - current["threshold"]) / span) * 100))
    return {"current_level": current["level"], "next_level": next_level["level"], "percent": percent, "trust_to_next_level": max(next_level["threshold"] - trust_score, 0), "levels": TRUST_LADDER}


def _member_display_name(user: User | None) -> str:
    if not user:
        return "A member"
    attrs = getattr(getattr(user, "profile", None), "attributes", {}) or {}
    for key in ("display_name", "first_name", "name"):
        value = attrs.get(key)
        if value:
            return str(value).split()[0]
    local = (user.email or "member").split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return local.split()[0].title() if local else "Member"


def community_trust_summary(db: Session, *, user_id: int) -> dict:
    reputation = get_or_create_reputation(db, user_id)
    participation = participation_summary(db, user_id=user_id)
    ladder = trust_ladder_progress(reputation.trust_score)
    return {
        "label": "Community Trust",
        "star": participation.get("star", 0),
        "trust_score": reputation.trust_score,
        "trust_percent": min(100, reputation.trust_score),
        "verified_contributions": reputation.verified_contributions,
        "verifications_completed": reputation.verifications_completed,
        "verification_accuracy": reputation.verification_accuracy,
        "leadership_level": ladder["current_level"],
        "consistency_streak": reputation.consistency_streak,
        "next_level": ladder["next_level"],
        "progress": ladder,
        "calculation": [
            "Verified contributions increase Community Trust when community confirmations are completed.",
            "Verification work increases trust when you help confirm another member’s proof honestly.",
            "Consistency streaks show steady participation over time.",
            "STAR Community Credits record rewards; Community Trust records reliability and service.",
        ],
        "updated_at": reputation.updated_at.isoformat() if reputation.updated_at else None,
    }


def open_verification_requests(db: Session, *, current_user_id: int | None = None, limit: int = 10) -> list[dict]:
    query = db.query(Activity).filter(Activity.verification_status == "pending")
    if current_user_id is not None:
        query = query.filter(Activity.user_id != current_user_id)
    activities = query.order_by(Activity.timestamp.desc(), Activity.id.desc()).limit(max(1, min(limit, 50))).all()
    users = {u.id: u for u in db.query(User).filter(User.id.in_([a.user_id for a in activities if a.user_id])).all()} if activities else {}
    rows = []
    for activity in activities:
        meta = activity.metadata_ or {}
        verification_meta = meta.get("community_verification") or {}
        confirmations = successful_verification_count(db, activity.id)
        rows.append({
            "id": activity.id,
            "activity_id": activity.id,
            "labor_category": meta.get("labor_category_label") or LABOR_CATEGORIES.get(meta.get("labor_category"), "Community Labor"),
            "submitted_by": _member_display_name(users.get(activity.user_id)),
            "activity_type": activity.activity_type,
            "content": meta.get("content") or activity.activity_type.replace("_", " "),
            "status": activity.verification_status,
            "current_confirmations": confirmations,
            "required_confirmations": verification_meta.get("required", VERIFICATIONS_REQUIRED),
            "star_reward": FIRST_VERIFIER_STAR if confirmations == 0 else FOLLOWUP_VERIFIER_STAR,
            "submitted_at": activity.timestamp.isoformat() if activity.timestamp else None,
        })
    return rows


def recent_community_activity(db: Session, *, limit: int = 12) -> list[dict]:
    activities = db.query(Activity).filter(Activity.user_id.isnot(None)).order_by(Activity.timestamp.desc(), Activity.id.desc()).limit(max(1, min(limit, 50))).all()
    users = {u.id: u for u in db.query(User).filter(User.id.in_([a.user_id for a in activities if a.user_id])).all()} if activities else {}
    feed = []
    for activity in activities:
        name = _member_display_name(users.get(activity.user_id))
        action = activity.activity_type.replace("_", " ")
        if activity.activity_type == "community_verification":
            message = f"{name} earned STAR for helping verify community work."
        elif activity.verification_status == "pending":
            message = f"{name} submitted proof of {action}."
        elif activity.activity_type in {"swahili_lesson_completed", "language_lesson"}:
            message = f"{name} completed a Swahili lesson."
        elif activity.activity_type == "decolonization_lesson_completed":
            message = f"{name} completed a decolonization lesson."
        elif activity.activity_type == "share_verified":
            message = f"{name} completed a verified community share."
        else:
            message = f"{name} completed {action}."
        feed.append({"id": activity.id, "message": message, "activity_type": activity.activity_type, "status": activity.verification_status, "star_award": activity.star_award, "timestamp": activity.timestamp.isoformat() if activity.timestamp else None})
    return feed

STAR_REWARDS = [
    {"title": "Recognition Badge", "star_cost": 25, "reward_type": "badge"},
    {"title": "Bonus Educational Resource", "star_cost": 50, "reward_type": "resource"},
    {"title": "Language Practice Pack", "star_cost": 75, "reward_type": "language_content"},
    {"title": "Audiobook Access Token", "star_cost": 100, "reward_type": "audiobook_access"},
    {"title": "Community Raffle Entry", "star_cost": 150, "reward_type": "raffle"},
    {"title": "Early-Access Materials", "star_cost": 250, "reward_type": "early_access"},
]



def _identity_filter(user: User | None, guest_session_id: str | None):
    if user:
        return Activity.user_id == user.id
    return Activity.guest_session_id == guest_session_id


def _duplicate_scope(metadata: dict | None) -> str:
    metadata = metadata or {}
    explicit = metadata.get("duplicate_key") or metadata.get("completion_key")
    if explicit:
        return str(explicit)

    today = datetime.utcnow().date().isoformat()
    for key in ("day", "lesson_day", "date", "chapter_index", "book_id", "game", "fact_id", "word", "task_id", "referral_email", "url"):
        if metadata.get(key) is not None:
            return f"{key}:{metadata.get(key)}"
    return f"daily:{today}"


def find_duplicate_activity(
    db: Session,
    *,
    user: User | None,
    guest_session_id: str | None,
    activity_type_name: str,
    source_module: str,
    metadata: dict | None = None,
) -> Activity | None:
    normalized_type = (activity_type_name or "general_participation").strip().lower().replace(" ", "_")
    normalized_source = (source_module or "community").strip().lower()
    scope = _duplicate_scope(metadata)
    query = db.query(Activity).filter(
        _identity_filter(user, guest_session_id),
        Activity.activity_type == normalized_type,
        Activity.source_module == normalized_source,
    )
    candidates = query.order_by(Activity.timestamp.desc(), Activity.id.desc()).limit(100).all()
    for activity in candidates:
        if _duplicate_scope(activity.metadata_) == scope:
            return activity
    return None

def rank_progress(star: int, user_id: int | None = None) -> dict:
    if user_id is None:
        return {"current_rank": "Guest", "next_rank": "Registered User", "current_threshold": 0, "next_threshold": 0, "percent": 0}
    current = RANK_THRESHOLDS[0]
    next_rank = None
    for idx, threshold in enumerate(RANK_THRESHOLDS):
        if star >= threshold[0]:
            current = threshold
            next_rank = RANK_THRESHOLDS[idx + 1] if idx + 1 < len(RANK_THRESHOLDS) else None
    if not next_rank:
        return {"current_rank": current[1], "next_rank": "Max Rank", "current_threshold": current[0], "next_threshold": current[0], "percent": 100, "star_to_next_rank": 0}
    span = max(next_rank[0] - current[0], 1)
    percent = min(100, round(((star - current[0]) / span) * 100))
    return {"current_rank": current[1], "next_rank": next_rank[1], "current_threshold": current[0], "next_threshold": next_rank[0], "percent": percent, "star_to_next_rank": max(next_rank[0] - star, 0)}


def current_streak(activities: list[Activity]) -> int:
    dates = sorted({item.timestamp.date() for item in activities if item.timestamp}, reverse=True)
    if not dates:
        return 0
    today = datetime.utcnow().date()
    if dates[0] not in {today, today - timedelta(days=1)}:
        return 0
    streak = 0
    expected = dates[0]
    for day in dates:
        if day == expected:
            streak += 1
            expected = expected - timedelta(days=1)
    return streak


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

    logger.info("Participation activity received", extra={"activity_type": activity_type_name, "source_module": source_module, "user_id": user.id if user else None, "guest_session_id": guest.session_id if guest else None})
    duplicate = find_duplicate_activity(db, user=user, guest_session_id=guest.session_id if guest else None, activity_type_name=activity_type_name, source_module=source_module, metadata=metadata)
    if duplicate:
        logger.info("Participation duplicate detected", extra={"activity_id": duplicate.id, "activity_type": duplicate.activity_type, "user_id": duplicate.user_id, "guest_session_id": duplicate.guest_session_id})
        return duplicate

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
    db.add(ActivityAuditLog(activity_id=activity.id, actor_user_id=activity.user_id, action="participation_engine_award", before={}, after={"points": points, "star": star, "verification_status": verification_status, "notification": "queued"}))
    logger.info("Participation STAR awarded", extra={"activity_id": activity.id, "activity_type": activity.activity_type, "user_id": activity.user_id, "guest_session_id": activity.guest_session_id, "star_awarded": star})
    return activity


def _labor_category(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("_labor", "")
    return normalized if normalized in LABOR_CATEGORIES else "community"


def get_or_create_reputation(db: Session, user_id: int) -> CommunityReputation:
    reputation = db.query(CommunityReputation).filter(CommunityReputation.user_id == user_id).first()
    if not reputation:
        reputation = CommunityReputation(user_id=user_id)
        db.add(reputation)
        db.flush()
    return reputation


def _refresh_leadership_level(reputation: CommunityReputation) -> None:
    if reputation.trust_score >= 250:
        reputation.leadership_level = "Trusted Steward"
    elif reputation.trust_score >= 100:
        reputation.leadership_level = "Community Verifier"
    elif reputation.trust_score >= 25:
        reputation.leadership_level = "Reliable Helper"
    else:
        reputation.leadership_level = "Emerging Steward"
    reputation.updated_at = datetime.utcnow()


def create_labor_verification_request(
    db: Session,
    *,
    user: User,
    labor_category: str,
    activity_type_name: str,
    source_module: str,
    proof_url: str | None = None,
    metadata: dict | None = None,
) -> Activity:
    category = _labor_category(labor_category)
    activity_type = get_activity_type(db, activity_type_name)
    activity_type.verification_required = True
    metadata_payload = {
        **(metadata or {}),
        "labor_category": category,
        "labor_category_label": LABOR_CATEGORIES[category],
        "proof_url": proof_url,
        "community_verification": {
            "status": "pending",
            "required": VERIFICATIONS_REQUIRED,
            "successful": 0,
            "discord_thread_status": "pending_bot_thread",
        },
    }
    activity = Activity(
        user_id=user.id,
        activity_type=activity_type.name,
        source_module=(source_module or "community").strip().lower(),
        verification_status="pending",
        participation_points=activity_type.default_points,
        star_award=0,
        metadata_=metadata_payload,
    )
    db.add(activity)
    db.flush()
    db.add(VerificationRecord(activity_id=activity.id, status="pending", notes="Community verification requested."))
    db.add(ActivityHistory(activity_id=activity.id, user_id=user.id, event_type="verification_requested", description=f"{LABOR_CATEGORIES[category]} submitted for community verification."))
    db.add(ActivityAuditLog(activity_id=activity.id, actor_user_id=user.id, action="community_verification_requested", before={}, after=metadata_payload))
    return activity


def successful_verification_count(db: Session, activity_id: int) -> int:
    return (
        db.query(VerificationRecord)
        .filter(
            VerificationRecord.activity_id == activity_id,
            VerificationRecord.status == "community_confirmed",
            VerificationRecord.verified_by_user_id.isnot(None),
        )
        .count()
    )


def verify_labor_contribution(
    db: Session,
    *,
    activity_id: int,
    verifier: User,
    proof_url: str | None = None,
    notes: str = "",
) -> tuple[Activity, VerificationRecord, bool, int]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise ValueError("Contribution not found")
    if activity.user_id == verifier.id:
        raise ValueError("Members cannot verify their own contribution")
    if activity.verification_status == "verified":
        raise ValueError("Contribution is already verified")

    existing = (
        db.query(VerificationRecord)
        .filter(
            VerificationRecord.activity_id == activity.id,
            VerificationRecord.verified_by_user_id == verifier.id,
            VerificationRecord.status == "community_confirmed",
        )
        .first()
    )
    if existing:
        raise ValueError("Verifier already confirmed this contribution")

    before_count = successful_verification_count(db, activity.id)
    if before_count >= VERIFICATIONS_REQUIRED:
        raise ValueError("Contribution already has enough verifications")

    star_award = FIRST_VERIFIER_STAR if before_count == 0 else FOLLOWUP_VERIFIER_STAR
    verification = VerificationRecord(
        activity_id=activity.id,
        status="community_confirmed",
        verified_by_user_id=verifier.id,
        notes=notes or proof_url or "Community verifier confirmed proof.",
    )
    db.add(verification)
    verifier_activity = submit_activity(
        db,
        user=verifier,
        guest_session_id=None,
        activity_type_name="community_verification",
        source_module="community_verification",
        metadata={"verified_activity_id": activity.id, "verifier_slot": before_count + 1, "proof_url": proof_url},
    )
    verifier_activity.participation_points = star_award
    verifier_activity.star_award = star_award
    db.query(ParticipationPoint).filter(ParticipationPoint.activity_id == verifier_activity.id).update({"points": star_award}, synchronize_session=False)
    db.query(StarTransaction).filter(StarTransaction.activity_id == verifier_activity.id).update({"amount": star_award}, synchronize_session=False)
    verifier_reputation = get_or_create_reputation(db, verifier.id)
    verifier_reputation.verifications_completed += 1
    verifier_reputation.trust_score += star_award
    verifier_reputation.consistency_streak += 1
    _refresh_leadership_level(verifier_reputation)

    after_count = before_count + 1
    completed = after_count >= VERIFICATIONS_REQUIRED
    metadata = dict(activity.metadata_ or {})
    verification_meta = dict(metadata.get("community_verification") or {})
    verification_meta.update({"status": "verified" if completed else "pending", "successful": after_count, "required": VERIFICATIONS_REQUIRED})
    metadata["community_verification"] = verification_meta
    activity.metadata_ = metadata

    if completed:
        activity_type = get_activity_type(db, activity.activity_type)
        activity.verification_status = "verified"
        activity.star_award = activity_type.default_star
        db.add(ParticipationPoint(activity_id=activity.id, user_id=activity.user_id, points=activity.participation_points, reason=activity.activity_type))
        db.add(StarTransaction(activity_id=activity.id, user_id=activity.user_id, amount=activity.star_award, transaction_type="earn", reason=activity.activity_type))
        db.add(ActivityHistory(activity_id=activity.id, user_id=activity.user_id, event_type="community_verified", description="Community verification completed with three confirmations."))
        contributor_reputation = get_or_create_reputation(db, activity.user_id)
        contributor_reputation.verified_contributions += 1
        contributor_reputation.trust_score += activity.star_award
        contributor_reputation.consistency_streak += 1
        _refresh_leadership_level(contributor_reputation)

    db.add(ActivityAuditLog(activity_id=activity.id, actor_user_id=verifier.id, action="community_verification_confirmed", before={"successful": before_count}, after={"successful": after_count, "completed": completed, "verifier_star": star_award}))
    return activity, verification, completed, star_award


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
    progress = rank_progress(star, user_id)
    return {"activity_count": len(activities), "activities_completed": len(activities), "participation_score": score, "star": star, "current_rank": progress["current_rank"], "current_streak": current_streak(activities), "rank_progress": progress}


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


def activity_history(db: Session, user_id: int | None = None, guest_session_id: str | None = None, limit: int = 25) -> list[Activity]:
    query = db.query(Activity)
    if user_id is not None:
        query = query.filter(Activity.user_id == user_id)
    elif guest_session_id:
        query = query.filter(Activity.guest_session_id == guest_session_id)
    else:
        return []
    return query.order_by(Activity.timestamp.desc(), Activity.id.desc()).limit(max(1, min(limit, 100))).all()


def available_opportunities() -> list[dict]:
    return STAR_OPPORTUNITIES


def available_rewards(star: int) -> list[dict]:
    return [{**reward, "unlocked": star >= reward["star_cost"], "star_needed": max(reward["star_cost"] - star, 0)} for reward in STAR_REWARDS]


def community_leaderboards(db: Session) -> dict:
    since = datetime.utcnow() - timedelta(days=7)

    def rows(filters=()):
        query = (db.query(Activity.user_id, func.coalesce(func.sum(Activity.star_award), 0).label("star"), func.count(Activity.id).label("activities"))
            .filter(Activity.user_id.isnot(None), Activity.timestamp >= since, Activity.verification_status == "verified"))
        for condition in filters:
            query = query.filter(condition)
        return [{"user_id": user_id, "star": int(star or 0), "activities": int(count or 0)} for user_id, star, count in query.group_by(Activity.user_id).order_by(func.sum(Activity.star_award).desc()).limit(10).all()]

    return {
        "weekly_star_leaders": rows(),
        "top_readers": rows((Activity.source_module.in_(["books", "audiobooks"]),)),
        "top_learners": rows((Activity.source_module.in_(["swahili", "yoruba", "learning", "decolonization"]),)),
        "top_volunteers": rows((Activity.activity_type.in_(["volunteer_task_completed", "community_help", "event_attended"]),)),
        "top_referrers": rows((Activity.activity_type == "member_referred",)),
    }
