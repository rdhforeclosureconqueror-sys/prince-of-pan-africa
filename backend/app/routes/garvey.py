from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_auth
from app.models import MemberProfile, User
from app.routes.member import _membership_type_from_subscription
from app.services.billing import latest_subscription_for_user
from app.services.participation import find_duplicate_activity, submit_activity

router = APIRouter(prefix="/member/assessments", tags=["Garvey Assessments"])
callback_router = APIRouter(prefix="/api/simbawajuma", tags=["Garvey Assessments"])


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _sign(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    head = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
    return f"{head}.{body}.{_b64url(signature)}"


def _configured_garvey_base() -> str:
    base = settings.GARVEY_BASE_URL.strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="Assessment Center is not configured yet.")
    return base


def _member_profile(db: Session, user: User) -> MemberProfile:
    profile = db.query(MemberProfile).filter(MemberProfile.user_id == user.id).first()
    if not profile:
        profile = MemberProfile(user_id=user.id, role=user.role or "member", attributes={})
        db.add(profile)
        db.flush()
    return profile


def _display_name(user: User, profile: MemberProfile | None) -> str:
    attrs = profile.attributes if profile else {}
    for key in ("display_name", "name", "first_name"):
        if attrs.get(key):
            return str(attrs[key])
    return (user.email or "Member").split("@", 1)[0].replace(".", " ").replace("_", " ").title()


class TransferTokenPayload(BaseModel):
    redirect_assessment: str | None = Field(default=None, max_length=160)


class GarveyCompletionPayload(BaseModel):
    event: str
    issuer: str | None = None
    external_user_id: str | int
    external_membership_id: str | int | None = None
    assessment_type: str
    assessment_name: str
    result_id: str
    primary_result: dict | str | None = None
    recommended_next_steps: list | dict | str | None = None
    star_reward_eligible: bool = False
    completed_at: datetime | None = None


@router.get("/catalog")
def get_assessment_catalog(current_user: User = Depends(require_auth)):
    base = _configured_garvey_base()
    del current_user
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(urljoin(f"{base}/", "api/simbawajuma/assessments"))
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Assessment catalog is temporarily unavailable.") from exc
    return response.json()


@router.post("/transfer-token")
def create_transfer_token(
    payload: TransferTokenPayload,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not settings.GARVEY_TRANSFER_SECRET.strip():
        raise HTTPException(status_code=503, detail="Assessment transfer is not configured yet.")
    base = _configured_garvey_base()
    user = db.query(User).options(joinedload(User.profile)).filter(User.id == current_user.id).first() or current_user
    profile = _member_profile(db, user)
    subscription = latest_subscription_for_user(db, user.id)
    membership_type = _membership_type_from_subscription(subscription)
    membership_status = "active" if subscription and membership_type != "free_member" else "free"
    now = datetime.now(timezone.utc)
    token_payload = {
        "issuer": settings.GARVEY_ALLOWED_ISSUER or "simba_wajuma",
        "external_user_id": str(user.id),
        "external_membership_id": str(subscription.id if subscription else f"simba-{user.id}"),
        "email": user.email,
        "display_name": _display_name(user, profile),
        "simba_role": profile.role or user.role or "member",
        "membership_status": membership_status,
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    if payload.redirect_assessment:
        token_payload["redirect_assessment"] = payload.redirect_assessment
    return {"ok": True, "token": _sign(token_payload, settings.GARVEY_TRANSFER_SECRET), "start_url": f"{base}/simbawajuma/start"}


@router.get("/results")
def get_assessment_results(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = _member_profile(db, current_user)
    completions = list((profile.attributes or {}).get("garvey_assessment_completions", []))
    return {"ok": True, "results": completions}


@callback_router.post("/assessment-callback")
def garvey_assessment_callback(
    payload: GarveyCompletionPayload,
    x_garvey_callback_secret: str | None = Header(default=None, alias="X-Garvey-Callback-Secret"),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    expected_secret = settings.GARVEY_CALLBACK_SECRET.strip()
    bearer = authorization.removeprefix("Bearer ").strip() if authorization else None
    if not expected_secret or not hmac.compare_digest(x_garvey_callback_secret or bearer or "", expected_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Garvey callback secret")
    if payload.event != "assessment.completed":
        raise HTTPException(status_code=400, detail="Unsupported Garvey assessment event")
    if settings.GARVEY_ALLOWED_ISSUER and payload.issuer and payload.issuer != settings.GARVEY_ALLOWED_ISSUER:
        raise HTTPException(status_code=403, detail="Unsupported Garvey issuer")

    try:
        simba_user_id = int(payload.external_user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Simba member id") from exc
    user = db.query(User).filter(User.id == simba_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Simba member not found")
    profile = _member_profile(db, user)
    completed_at = payload.completed_at or datetime.utcnow()
    completion = {
        "assessment_type": payload.assessment_type,
        "assessment_name": payload.assessment_name,
        "result_id": payload.result_id,
        "primary_result": payload.primary_result,
        "recommended_next_steps": payload.recommended_next_steps,
        "star_reward_eligible": payload.star_reward_eligible,
        "completed_at": completed_at.isoformat(),
    }
    attributes = dict(profile.attributes or {})
    previous_completions = attributes.get("garvey_assessment_completions", [])
    if not isinstance(previous_completions, list):
        previous_completions = []
    existing = [item for item in previous_completions if isinstance(item, dict) and item.get("result_id") != payload.result_id]
    attributes["garvey_assessment_completions"] = [completion, *existing][:25]
    profile.attributes = attributes
    flag_modified(profile, "attributes")

    activity = None
    duplicate = None
    if payload.star_reward_eligible:
        metadata = {"result_id": payload.result_id, "assessment_type": payload.assessment_type, "completion_key": f"garvey:{payload.result_id}"}
        duplicate = find_duplicate_activity(db, user=user, guest_session_id=None, activity_type_name="quiz_completed", source_module="assessment_center", metadata=metadata)
        activity = submit_activity(db, user=user, guest_session_id=None, activity_type_name="quiz_completed", source_module="assessment_center", metadata=metadata)
    db.commit()
    return {"ok": True, "stored": completion, "star_awarded": bool(activity and not duplicate), "activity_id": activity.id if activity else None}
