from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified

from app.dependencies.auth import require_permission
from app.database import get_db
from app.models import ActivityLog, LeadershipAssessment, MemberProfile, Subscription, User
from app.services.billing import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    BUILDER_TIER,
    COMMUNITY_TIER,
    PAID_ACCESS_TIERS,
    latest_subscription_for_user,
)

router = APIRouter(tags=["Member"])


def _membership_type_from_subscription(subscription: Subscription | None) -> str:
    subscription_status = (subscription.status or "").strip().lower() if subscription else ""
    subscription_tier = (subscription.tier or "").strip().lower() if subscription else ""
    if subscription_status in ACTIVE_SUBSCRIPTION_STATUSES and subscription_tier in PAID_ACCESS_TIERS:
        return subscription_tier
    return "free_member"


def _membership_label(membership_type: str) -> str:
    if membership_type == BUILDER_TIER:
        return "Builder Member (Paid)"
    if membership_type == COMMUNITY_TIER:
        return "Community Member (Paid)"
    return "Free Member"


@router.get("/member/overview")
def get_member_overview(
    current_user: User = Depends(require_permission("member:read_overview_self")),
    db: Session = Depends(get_db),
):
    user = db.query(User).options(joinedload(User.profile)).filter(User.id == current_user.id).first()

    profile = user.profile
    profile_attributes = profile.attributes if profile else {}
    subscription = latest_subscription_for_user(db, user.id)
    membership_type = _membership_type_from_subscription(subscription)
    subscription_status = (subscription.status or "").strip().lower() if subscription else None
    is_paid_member = membership_type in PAID_ACCESS_TIERS
    is_builder = membership_type == BUILDER_TIER

    assessment_count = (
        db.query(LeadershipAssessment)
        .filter(LeadershipAssessment.user_id == user.id)
        .count()
    )

    activity_count = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .count()
    )

    # Canonical summary block (additive; older fields are preserved below).
    summary_stats = {
        "assessment_count": assessment_count,
        "activity_count": activity_count,
        "reading_minutes": 0,
        "workouts_completed": 0,
        "shares": 0,
        "streak_days": 0,
    }

    return {
        "ok": True,
        "status": "ok",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "member_profile": {
            "id": profile.id if profile else None,
            "role": (profile.role if profile else user.role),
            "attributes": profile_attributes,
        },
        "membership": {
            "status": "active" if is_paid_member else "free",
            "type": membership_type,
            "label": _membership_label(membership_type),
            "stripe_confirmed": is_paid_member,
            "subscription_status": subscription_status,
            "orientation_status": profile_attributes.get("orientation_status", "not_started"),
            "discord_status": profile_attributes.get("discord_status", "not_connected"),
            "community_updates": [
                "Foundation Binder locked through Section 6.",
                "Community and Builder membership structure is being prepared for launch.",
                "Stripe and Discord integrations are planned next, but not active yet.",
            ],
            "builder": {
                "is_builder": is_builder,
                "activation": profile_attributes.get("builder_activation", {}),
                "onboarding_completed": bool(profile_attributes.get("onboarding_completed", False)),
                "first_challenge_completed": bool(profile_attributes.get("first_challenge_completed", False)),
                "first_contribution_completed": bool(profile_attributes.get("first_contribution_completed", False)),
                "builder_level": profile_attributes.get("builder_level", "not_started" if is_builder else "community_only"),
                "testing_opportunities": [
                    "Review the member onboarding flow.",
                    "Test library and foundational learning paths.",
                    "Share feedback on Builder participation workflows.",
                ] if is_builder else [],
                "contribution_history": profile_attributes.get("builder_contribution_history", []),
                "feedback_participation": {
                    "status": "ready" if is_builder else "community_only",
                    "summary": "Builder feedback tracking is prepared for launch planning." if is_builder else "Upgrade to Builder Membership to participate in Builder feedback workflows.",
                },
            },
        },
        "summary_stats": summary_stats,
        # Backward-compatible top-level keys currently read by MemberDashboard.jsx.
        "reading_minutes": summary_stats["reading_minutes"],
        "workouts_completed": summary_stats["workouts_completed"],
        "shares": summary_stats["shares"],
        "streak_days": summary_stats["streak_days"],
    }


@router.post("/member/builder/onboarding")
def save_builder_onboarding(
    payload: dict = Body(...),
    current_user: User = Depends(require_permission("builder:track_contributions")),
    db: Session = Depends(get_db),
):
    subscription = latest_subscription_for_user(db, current_user.id)
    if _membership_type_from_subscription(subscription) != BUILDER_TIER:
        raise HTTPException(status_code=403, detail="Active Builder Membership is required.")

    profile = db.query(MemberProfile).filter(MemberProfile.user_id == current_user.id).first()
    if not profile:
        profile = MemberProfile(user_id=current_user.id, role=current_user.role or "builder_member", attributes={})
        db.add(profile)
        db.flush()

    completed = bool(payload.get("completed", False))
    try:
        current_step = int(payload.get("current_step", 0) or 0)
    except (TypeError, ValueError):
        current_step = 0

    activation = {
        "introduction": str(payload.get("introduction", "")).strip(),
        "interests": [str(item).strip() for item in payload.get("interests", []) if str(item).strip()],
        "team": str(payload.get("team", "")).strip(),
        "first_challenge": str(payload.get("first_challenge", "")).strip(),
        "first_contribution": str(payload.get("first_contribution", "")).strip(),
        "current_step": max(0, min(current_step, 6)),
        "steps_completed": payload.get("steps_completed", []),
    }
    if completed and (
        not activation["introduction"]
        or not activation["interests"]
        or not activation["team"]
        or not activation["first_challenge"]
        or not activation["first_contribution"]
    ):
        raise HTTPException(status_code=422, detail="All Builder activation steps are required before completion.")

    attributes = dict(profile.attributes or {})
    already_completed = bool(attributes.get("onboarding_completed", False))
    first_challenge_completed = bool(attributes.get("first_challenge_completed", False)) or bool(payload.get("first_challenge_completed", False))
    first_contribution_completed = bool(attributes.get("first_contribution_completed", False)) or bool(payload.get("first_contribution_completed", False))
    onboarding_completed = already_completed or completed

    attributes["builder_activation"] = activation
    attributes["orientation_status"] = "completed" if onboarding_completed else "in_progress"
    attributes["onboarding_completed"] = onboarding_completed
    attributes["first_challenge_completed"] = first_challenge_completed
    attributes["first_contribution_completed"] = first_contribution_completed
    attributes["builder_level"] = "activated_builder" if onboarding_completed else "activation_in_progress"

    if completed and not already_completed:
        attributes["builder_contribution_history"] = [
            {"title": "Builder activation completed", "summary": activation["first_contribution"]}
        ]

    profile.attributes = attributes
    flag_modified(profile, "attributes")
    db.add(ActivityLog(user_id=current_user.id, action="builder_onboarding_completed" if completed else "builder_onboarding_saved"))
    db.commit()

    return {
        "ok": True,
        "onboarding_completed": attributes["onboarding_completed"],
        "first_challenge_completed": attributes["first_challenge_completed"],
        "first_contribution_completed": attributes["first_contribution_completed"],
        "builder_level": attributes["builder_level"],
        "activation": activation,
    }


@router.get("/member/activity")
def get_member_activity(
    limit: int = 10,
    current_user: User = Depends(require_permission("member:read_activity_self")),
    db: Session = Depends(get_db),
):

    entries = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(max(1, min(limit, 50)))
        .all()
    )

    # Canonical item shape with compatibility aliases for existing frontend callers.
    activity_items = [
        {
            "id": entry.id,
            "action": entry.action,
            "title": entry.action,
            "type": entry.action,
            "description": entry.action,
            "detail": entry.action,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        }
        for entry in entries
    ]

    return {
        "ok": True,
        "status": "ok",
        "user_id": current_user.id,
        "activity": activity_items,
        "items": activity_items,
    }
