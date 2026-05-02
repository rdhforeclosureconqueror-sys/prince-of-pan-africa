from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_permission
from app.models import (
    ActivityLog,
    Audiobook,
    AudiobookChapterReflection,
    AudiobookProgress,
    LeadershipAssessment,
    MemberProfile,
    User,
)

router = APIRouter(prefix="/admin/ai", tags=["Admin AI"])


def _build_overview_metrics(db: Session) -> dict:
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    users_by_role_rows = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role: count for role, count in users_by_role_rows}

    metrics = {
        "total_users": {"value": db.query(func.count(User.id)).scalar() or 0, "source": "real"},
        "users_by_role": {"value": users_by_role, "source": "real"},
        "total_member_profiles": {"value": db.query(func.count(MemberProfile.id)).scalar() or 0, "source": "real"},
        "total_activity_logs": {"value": db.query(func.count(ActivityLog.id)).scalar() or 0, "source": "real"},
        "total_leadership_assessments": {
            "value": db.query(func.count(LeadershipAssessment.id)).scalar() or 0,
            "source": "real",
        },
        "total_audiobooks": {"value": db.query(func.count(Audiobook.id)).scalar() or 0, "source": "real"},
        "total_audiobook_progress_records": {
            "value": db.query(func.count(AudiobookProgress.id)).scalar() or 0,
            "source": "real",
        },
        "total_reflections": {
            "value": db.query(func.count(AudiobookChapterReflection.id)).scalar() or 0,
            "source": "real",
        },
        "new_users_last_7_days": {
            "value": db.query(func.count(User.id)).filter(User.created_at >= seven_days_ago).scalar() or 0,
            "source": "real",
        },
        "active_users_last_7_days": {
            "value": db.query(func.count(func.distinct(ActivityLog.user_id)))
            .filter(ActivityLog.timestamp >= seven_days_ago)
            .scalar()
            or 0,
            "source": "real",
        },
    }

    return metrics


@router.get("/overview")
def admin_ai_overview(
    _: None = Depends(require_permission("admin:read_dashboard")),
    db: Session = Depends(get_db),
):
    metrics = _build_overview_metrics(db)
    return {
        "ok": True,
        "data": {
            "source": "placeholder_removed",
            "metrics": metrics,
        },
    }


@router.get("/members")
def admin_ai_members(_: None = Depends(require_permission("admin:read_users"))):
    return {"ok": True, "members": []}


@router.get("/profiles")
def admin_ai_profiles(_: None = Depends(require_permission("admin:read_users"))):
    return {"ok": True, "profiles": []}


# Backward-compatible admin surfaces used by legacy and pilot dashboards.
legacy_router = APIRouter(prefix="/admin", tags=["Admin Compatibility"])


@legacy_router.get("/overview")
def admin_overview_compat(
    _: None = Depends(require_permission("admin:read_dashboard")),
    db: Session = Depends(get_db),
):
    metrics = _build_overview_metrics(db)
    return {
        "ok": True,
        "data": {
            "source": "placeholder_removed",
            "metrics": metrics,
        },
    }


@legacy_router.get("/members")
def admin_members_compat(_: None = Depends(require_permission("admin:read_users"))):
    return {"ok": True, "members": []}


@legacy_router.get("/profiles")
def admin_profiles_compat(_: None = Depends(require_permission("admin:read_users"))):
    return {"ok": True, "profiles": []}


@legacy_router.get("/shares")
def admin_shares_compat(_: None = Depends(require_permission("admin:manage_users"))):
    return {"ok": True, "shares": []}


@legacy_router.get("/reviews")
def admin_reviews_compat(_: None = Depends(require_permission("admin:manage_users"))):
    return {"ok": True, "reviews": []}


@legacy_router.get("/activity-stream")
def admin_activity_stream_compat(
    _: None = Depends(require_permission("admin:read_activity")),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(ActivityLog)
        .order_by(ActivityLog.timestamp.desc(), ActivityLog.id.desc())
        .limit(50)
        .all()
    )
    return {
        "ok": True,
        "source": "placeholder_removed",
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "action": item.action,
                "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                "data_source": "real",
            }
            for item in activities
        ],
    }


@legacy_router.get("/holistic/overview")
def admin_holistic_overview_compat(_: None = Depends(require_permission("admin:read_dashboard"))):
    return {"ok": True, "holistic": []}
