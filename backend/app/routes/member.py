from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.dependencies.auth import require_permission
from app.database import get_db
from app.models import ActivityLog, LeadershipAssessment, User

router = APIRouter(tags=["Member"])


@router.get("/member/overview")
def get_member_overview(
    current_user: User = Depends(require_permission("member:read_overview_self")),
    db: Session = Depends(get_db),
):
    user = db.query(User).options(joinedload(User.profile)).filter(User.id == current_user.id).first()

    profile = user.profile

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
            "attributes": profile.attributes if profile else {},
        },
        "summary_stats": summary_stats,
        # Backward-compatible top-level keys currently read by MemberDashboard.jsx.
        "reading_minutes": summary_stats["reading_minutes"],
        "workouts_completed": summary_stats["workouts_completed"],
        "shares": summary_stats["shares"],
        "streak_days": summary_stats["streak_days"],
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
