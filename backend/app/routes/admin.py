from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_permission
from app.services.intelligence_health import diagnostic_history, generate_public_diagnostic_report, get_public_diagnostic_report, public_diagnostic_error, public_report_to_markdown, run_full_intelligence_diagnostic, validate_public_report_token
from app.models import (
    ActivityLog,
    Audiobook,
    AudiobookChapterReflection,
    AudiobookProgress,
    ContentShare,
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
public_router = APIRouter(tags=["Public Intelligence Diagnostics"])


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
def admin_shares_compat(
    _: None = Depends(require_permission("admin:manage_users")),
    db: Session = Depends(get_db),
):
    rows = db.query(ContentShare).order_by(ContentShare.created_at.desc()).limit(100).all()
    return {
        "ok": True,
        "shares": [
            {
                "share_id": row.share_id,
                "member_id": row.user_id,
                "visitor_id": row.visitor_id,
                "content_type": row.content_type,
                "content_id": row.content_id,
                "share_platform": "native",
                "share_url": f"{row.target_url}{'&' if '?' in row.target_url else '?'}swu_share={row.share_id}",
                "click_count": row.click_count,
                "visitor_count": row.visitor_count,
                "registration_count": row.registration_count,
                "membership_count": row.membership_count,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


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


@legacy_router.post("/intelligence-health/run")
def run_intelligence_health_diagnostic(_: None = Depends(require_permission("admin:read_dashboard"))):
    return run_full_intelligence_diagnostic()


@legacy_router.get("/intelligence-health/history")
def get_intelligence_health_history(_: None = Depends(require_permission("admin:read_dashboard"))):
    return {"ok": True, "history": diagnostic_history()}


@legacy_router.post("/intelligence-health/public-report")
def create_public_intelligence_health_report(_: None = Depends(require_permission("admin:read_dashboard"))):
    run = run_full_intelligence_diagnostic()
    report = generate_public_diagnostic_report(run)
    return {"ok": True, "report": report}



def _safe_public_report_or_error(token: str):
    if not validate_public_report_token(token):
        raise HTTPException(status_code=400, detail=public_diagnostic_error("Public diagnostic report token is malformed or missing.", "malformed_public_report_token"))
    report = get_public_diagnostic_report(token)
    if not report:
        raise HTTPException(status_code=404, detail=public_diagnostic_error("Public diagnostic report not found.", "public_report_not_found"))
    if report.get("expiration_status") == "expired":
        raise HTTPException(status_code=410, detail=public_diagnostic_error("Public diagnostic report has expired.", "public_report_expired"))
    return report


@public_router.get("/public/intelligence-diagnostics/{token}.json")
def get_public_intelligence_health_report_json(token: str):
    return _safe_public_report_or_error(token)


@public_router.get("/public/intelligence-diagnostics/{token}.md", response_class=PlainTextResponse)
def get_public_intelligence_health_report_markdown(token: str):
    return PlainTextResponse(public_report_to_markdown(_safe_public_report_or_error(token)), media_type="text/markdown; charset=utf-8")


@public_router.get("/public/intelligence-diagnostics/{token}")
def get_public_intelligence_health_report(token: str):
    return _safe_public_report_or_error(token)
