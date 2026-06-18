from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_auth
from app.models import Activity, CommunityReputation
from app.services.participation import (
    activity_history,
    available_opportunities,
    available_rewards,
    community_leaderboards,
    community_trust_summary,
    create_labor_verification_request,
    find_duplicate_activity,
    get_or_create_reputation,
    open_verification_requests,
    participation_summary,
    submit_activity,
    recent_community_activity,
    successful_verification_count,
    verify_labor_contribution,
)

router = APIRouter(prefix="/participation", tags=["Participation"])


class ActivityPayload(BaseModel):
    activity_type: str = Field(min_length=1, max_length=128)
    source_module: str = Field(min_length=1, max_length=128)
    guest_session_id: str | None = Field(default=None, max_length=128)
    metadata: dict = Field(default_factory=dict)


class VerificationRequestPayload(BaseModel):
    labor_category: str = Field(default="growth", max_length=32)
    activity_type: str = Field(default="share_verified", min_length=1, max_length=128)
    source_module: str = Field(default="growth", min_length=1, max_length=128)
    content: str = Field(default="", max_length=255)
    proof_url: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)


class VerificationConfirmPayload(BaseModel):
    proof_url: str | None = Field(default=None, max_length=500)
    notes: str = Field(default="", max_length=1000)


def _serialize_activity(activity: Activity) -> dict:
    return {
        "id": activity.id,
        "activity_id": activity.id,
        "user_id": activity.user_id,
        "guest_session_id": activity.guest_session_id,
        "activity_type": activity.activity_type,
        "source_module": activity.source_module,
        "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
        "verification_status": activity.verification_status,
        "participation_points": activity.participation_points,
        "star_award": activity.star_award,
        "metadata": activity.metadata_,
    }


def _serialize_reputation(reputation: CommunityReputation) -> dict:
    return {
        "user_id": reputation.user_id,
        "verified_contributions": reputation.verified_contributions,
        "verifications_completed": reputation.verifications_completed,
        "verification_accuracy": reputation.verification_accuracy,
        "trust_score": reputation.trust_score,
        "leadership_level": reputation.leadership_level,
        "consistency_streak": reputation.consistency_streak,
        "updated_at": reputation.updated_at.isoformat() if reputation.updated_at else None,
    }


@router.post("/activity")
def create_participation_activity(
    payload: ActivityPayload,
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = payload.guest_session_id or x_guest_session_id or request.cookies.get("simba_guest_session")
    duplicate = find_duplicate_activity(
        db,
        user=current_user,
        guest_session_id=guest_session_id,
        activity_type_name=payload.activity_type,
        source_module=payload.source_module,
        metadata=payload.metadata,
    ) if (current_user or guest_session_id) else None
    activity = submit_activity(
        db,
        user=current_user,
        guest_session_id=guest_session_id,
        activity_type_name=payload.activity_type,
        source_module=payload.source_module,
        metadata=payload.metadata,
    )
    was_duplicate = duplicate is not None or activity.id == getattr(duplicate, "id", None)
    summary = participation_summary(db, user_id=current_user.id if current_user else None, guest_session_id=activity.guest_session_id)
    db.commit()
    awarded_star = 0 if was_duplicate else activity.star_award
    message = "You already earned STAR for this activity." if was_duplicate else "STAR Community Credits awarded. Your progress has been saved."
    return {"ok": True, "duplicate": was_duplicate, "awarded_star": awarded_star, "message": message, "activity": _serialize_activity(activity), "participation": summary}


@router.get("/summary")
def get_participation_summary(
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = x_guest_session_id or request.cookies.get("simba_guest_session")
    summary = participation_summary(db, user_id=current_user.id if current_user else None, guest_session_id=guest_session_id)
    return {"ok": True, "participation": summary}


@router.get("/experience")
def get_star_experience(
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = x_guest_session_id or request.cookies.get("simba_guest_session")
    user_id = current_user.id if current_user else None
    summary = participation_summary(db, user_id=user_id, guest_session_id=guest_session_id)
    history = [_serialize_activity(item) for item in activity_history(db, user_id=user_id, guest_session_id=guest_session_id, limit=25)]
    return {
        "ok": True,
        "participation": summary,
        "opportunities": available_opportunities(),
        "history": history,
        "rewards": available_rewards(summary["star"]),
        "leaderboards": community_leaderboards(db),
    }


@router.get("/opportunities")
def get_star_opportunities():
    return {"ok": True, "opportunities": available_opportunities()}


@router.get("/history")
def get_activity_history(
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = x_guest_session_id or request.cookies.get("simba_guest_session")
    user_id = current_user.id if current_user else None
    return {"ok": True, "history": [_serialize_activity(item) for item in activity_history(db, user_id=user_id, guest_session_id=guest_session_id, limit=limit)]}


@router.get("/rewards")
def get_star_rewards(
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = x_guest_session_id or request.cookies.get("simba_guest_session")
    summary = participation_summary(db, user_id=current_user.id if current_user else None, guest_session_id=guest_session_id)
    return {"ok": True, "rewards": available_rewards(summary["star"])}


@router.get("/leaderboards")
def get_community_leaderboards(db: Session = Depends(get_db)):
    return {"ok": True, "leaderboards": community_leaderboards(db)}


@router.post("/verification-requests", status_code=status.HTTP_201_CREATED)
def create_community_verification_request(
    payload: VerificationRequestPayload,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    metadata = {
        **payload.metadata,
        "content": payload.content,
        "discord_workflow": {
            "channel": "verification",
            "thread_title": "New Share Verification Request" if payload.activity_type == "share_verified" else "New Community Verification Request",
            "status": "pending_discord_bot",
        },
    }
    activity = create_labor_verification_request(
        db,
        user=current_user,
        labor_category=payload.labor_category,
        activity_type_name=payload.activity_type,
        source_module=payload.source_module,
        proof_url=payload.proof_url,
        metadata=metadata,
    )
    reputation = get_or_create_reputation(db, current_user.id)
    db.commit()
    return {
        "ok": True,
        "message": "Community verification request created. Three member confirmations are required before STAR is awarded.",
        "activity": _serialize_activity(activity),
        "verification": {"required": 3, "successful": 0, "status": "pending"},
        "reputation": _serialize_reputation(reputation),
    }


@router.post("/verification-requests/{activity_id}/verify")
def confirm_community_verification(
    activity_id: int,
    payload: VerificationConfirmPayload,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    try:
        activity, verification, completed, verifier_star = verify_labor_contribution(
            db,
            activity_id=activity_id,
            verifier=current_user,
            proof_url=payload.proof_url,
            notes=payload.notes,
        )
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if detail == "Contribution not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail) from exc

    contributor_reputation = get_or_create_reputation(db, activity.user_id)
    verifier_reputation = get_or_create_reputation(db, current_user.id)
    confirmations = successful_verification_count(db, activity.id)
    db.commit()
    return {
        "ok": True,
        "completed": completed,
        "message": "Contribution verified and thread ready to close." if completed else "Verification recorded. Additional confirmations are still needed.",
        "verifier_awarded_star": verifier_star,
        "activity": _serialize_activity(activity),
        "verification": {
            "id": verification.id,
            "required": 3,
            "successful": confirmations,
            "status": activity.verification_status,
        },
        "contributor_reputation": _serialize_reputation(contributor_reputation),
        "verifier_reputation": _serialize_reputation(verifier_reputation),
    }


@router.get("/reputation")
def get_my_community_reputation(db: Session = Depends(get_db), current_user=Depends(require_auth)):
    reputation = get_or_create_reputation(db, current_user.id)
    db.commit()
    return {"ok": True, "reputation": _serialize_reputation(reputation)}


@router.get("/community-trust")
def get_community_trust_dashboard(db: Session = Depends(get_db), current_user=Depends(require_auth)):
    trust = community_trust_summary(db, user_id=current_user.id)
    db.commit()
    return {"ok": True, "community_trust": trust}


@router.get("/verification-requests/open")
def get_open_verification_requests(limit: int = 10, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    return {"ok": True, "verification_requests": open_verification_requests(db, current_user_id=current_user.id, limit=limit)}


@router.get("/community-activity/recent")
def get_recent_community_labor_activity(limit: int = 12, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    return {"ok": True, "activity": recent_community_activity(db, limit=limit)}
