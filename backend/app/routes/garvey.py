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
from app.models import GarveySyncEvent, MemberProfile, User
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
    event: str = "assessment.completed"
    issuer: str | None = None
    external_user_id: str | int = Field(alias="member_id")
    external_membership_id: str | int | None = None
    assessment_type: str | None = None
    assessment_id: str | None = None
    assessment_name: str
    result_id: str | None = None
    completion_status: str = "completed"
    overall_score: float | None = None
    percentile: float | None = None
    strengths: list[str] = Field(default_factory=list)
    opportunities_for_growth: list[str] = Field(default_factory=list)
    recommended_next_assessment: str | None = None
    recommendation_confidence: float | None = None
    primary_result: dict | str | None = None
    recommended_next_steps: list | dict | str | None = None
    star_reward_eligible: bool = False
    completed_at: datetime | None = None

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


def _payload_json(payload: BaseModel) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json")
    return json.loads(payload.json())


GROWTH_CATEGORIES = [
    "Leadership",
    "Cooperative Economics",
    "Entrepreneurship",
    "Financial Literacy",
    "Community Participation",
    "Learning Style",
    "Personality",
    "Rite of Passage",
    "Future Assessments",
]

BADGE_RULES = [
    ("first_assessment", "First Assessment", lambda profile: profile["summary"]["completed_assessments"] >= 1),
    ("leadership_certified", "Leadership Certified", lambda profile: _category_score(profile, "Leadership") >= 80),
    ("cooperative_economics_explorer", "Cooperative Economics Explorer", lambda profile: _category_attempts(profile, "Cooperative Economics") >= 1),
    ("entrepreneur_ready", "Entrepreneur Ready", lambda profile: _category_score(profile, "Entrepreneurship") >= 80),
    ("community_builder", "Community Builder", lambda profile: _category_score(profile, "Community Participation") >= 70),
    ("lifelong_learner", "Lifelong Learner", lambda profile: profile["summary"]["total_attempts"] >= 3),
]


def _category_from_payload(payload: GarveyCompletionPayload) -> str:
    raw = (payload.assessment_type or payload.assessment_name or "Future Assessments").replace("_", " " ).lower()
    if "leadership" in raw:
        return "Leadership"
    if "economic" in raw or "cooperative" in raw:
        return "Cooperative Economics"
    if "entrepreneur" in raw or "business" in raw:
        return "Entrepreneurship"
    if "financial" in raw or "finance" in raw:
        return "Financial Literacy"
    if "community" in raw or "participation" in raw:
        return "Community Participation"
    if "learning" in raw:
        return "Learning Style"
    if "personality" in raw:
        return "Personality"
    if "rite" in raw or "passage" in raw:
        return "Rite of Passage"
    return "Future Assessments"


def _blank_growth_profile() -> dict:
    return {"categories": {name: {"assessments": {}, "latest_score": None, "status": "not_started"} for name in GROWTH_CATEGORIES}, "badges": [], "timeline": [], "summary": {"overall_completion": 0, "completed_assessments": 0, "total_attempts": 0}}


def _category_score(profile: dict, category: str) -> float:
    return float(profile.get("categories", {}).get(category, {}).get("latest_score") or 0)


def _category_attempts(profile: dict, category: str) -> int:
    return sum(int(item.get("attempts") or 0) for item in profile.get("categories", {}).get(category, {}).get("assessments", {}).values())


def _recommended_review_date(completed_at: datetime) -> str:
    return (completed_at + timedelta(days=90)).date().isoformat()


def _next_assessment(profile: dict, fallback: str | None) -> dict:
    if fallback:
        return {"assessment_name": fallback, "confidence": None, "reason": "Garvey recommended this from the latest result."}
    scores = {name: _category_score(profile, name) for name in GROWTH_CATEGORIES}
    if scores["Leadership"] and scores["Leadership"] < 70:
        return {"assessment_name": "Leadership Foundations", "confidence": 0.82, "reason": "Leadership score needs reinforcement."}
    if scores["Leadership"] >= 80 and not scores["Community Participation"]:
        return {"assessment_name": "Community Builder Assessment", "confidence": 0.78, "reason": "Strong leadership can be applied through community practice."}
    if scores["Cooperative Economics"] >= 80 and not scores["Entrepreneurship"]:
        return {"assessment_name": "Entrepreneur Assessment", "confidence": 0.76, "reason": "Economic strengths point toward venture readiness."}
    if scores["Entrepreneurship"] >= 80:
        return {"assessment_name": "Cooperative Governance", "confidence": 0.74, "reason": "Entrepreneurial strength is ready for shared-governance development."}
    return {"assessment_name": "Leadership Foundations", "confidence": 0.65, "reason": "A foundational assessment gives Garvey more signal."}


def _apply_assessment_completion(profile: dict, payload: GarveyCompletionPayload, completed_at: datetime) -> tuple[dict, dict]:
    growth = dict(profile or _blank_growth_profile())
    growth.setdefault("categories", _blank_growth_profile()["categories"])
    growth.setdefault("timeline", [])
    growth.setdefault("badges", [])
    category = _category_from_payload(payload)
    cat = growth["categories"].setdefault(category, {"assessments": {}, "latest_score": None, "status": "not_started"})
    assessments = cat.setdefault("assessments", {})
    assessment_id = payload.assessment_id or payload.assessment_type or payload.assessment_name
    current = assessments.get(assessment_id, {})
    score = payload.overall_score
    attempts = int(current.get("attempts") or 0) + 1
    record = {**current, "assessment_id": assessment_id, "assessment_name": payload.assessment_name, "latest_score": score, "highest_score": max([v for v in [current.get("highest_score"), score] if v is not None], default=None), "completion_date": completed_at.isoformat(), "attempts": attempts, "completion_status": payload.completion_status, "recommended_review_date": _recommended_review_date(completed_at), "percentile": payload.percentile, "strengths": payload.strengths, "opportunities_for_growth": payload.opportunities_for_growth}
    assessments[assessment_id] = record
    cat["latest_score"] = score
    cat["status"] = payload.completion_status
    recommendation = _next_assessment(growth, payload.recommended_next_assessment)
    if payload.recommendation_confidence is not None:
        recommendation["confidence"] = payload.recommendation_confidence
    record["recommended_next_assessment"] = recommendation
    growth["timeline"] = [{"assessment_id": assessment_id, "assessment_name": payload.assessment_name, "category": category, "score": score, "status": payload.completion_status, "completed_at": completed_at.isoformat()}, *[i for i in growth.get("timeline", []) if i.get("result_id") != payload.result_id]][:100]
    completed = sum(1 for item in growth["categories"].values() if item.get("status") == "completed")
    total_attempts = sum(_category_attempts(growth, name) for name in GROWTH_CATEGORIES)
    growth["summary"] = {"overall_completion": round((completed / len(GROWTH_CATEGORIES)) * 100), "completed_assessments": completed, "total_attempts": total_attempts, "recommended_next_assessment": recommendation}
    existing_badges = {badge.get("id"): badge for badge in growth.get("badges", []) if isinstance(badge, dict)}
    for badge_id, label, predicate in BADGE_RULES:
        if badge_id not in existing_badges and predicate(growth):
            existing_badges[badge_id] = {"id": badge_id, "label": label, "unlocked_at": completed_at.isoformat()}
    growth["badges"] = list(existing_badges.values())
    return growth, record


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
    attributes = profile.attributes or {}
    completions = list(attributes.get("garvey_assessment_completions", []))
    return {"ok": True, "results": completions, "growth_profile": attributes.get("growth_profile", _blank_growth_profile())}


@router.get("/growth-profile")
def get_growth_profile(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = _member_profile(db, current_user)
    return {"ok": True, "growth_profile": (profile.attributes or {}).get("growth_profile", _blank_growth_profile())}


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
        db.add(GarveySyncEvent(event_type=payload.event, external_user_id=str(payload.external_user_id), payload=_payload_json(payload), status="pending", retry_count=0, last_error="Simba member not found"))
        db.commit()
        return {"ok": False, "queued": True, "detail": "Simba member not found; queued for retry"}
    profile = _member_profile(db, user)
    completed_at = payload.completed_at or datetime.utcnow()
    attributes = dict(profile.attributes or {})
    growth_profile, assessment_record = _apply_assessment_completion(attributes.get("growth_profile", _blank_growth_profile()), payload, completed_at)
    completion = {
        "assessment_type": payload.assessment_type or _category_from_payload(payload).lower().replace(" ", "_"),
        "assessment_id": payload.assessment_id or payload.assessment_type or payload.assessment_name,
        "assessment_name": payload.assessment_name,
        "result_id": payload.result_id or payload.assessment_id or payload.assessment_name,
        "completion_status": payload.completion_status,
        "overall_score": payload.overall_score,
        "percentile": payload.percentile,
        "strengths": payload.strengths,
        "opportunities_for_growth": payload.opportunities_for_growth,
        "recommended_next_assessment": assessment_record.get("recommended_next_assessment"),
        "primary_result": payload.primary_result,
        "recommended_next_steps": payload.recommended_next_steps,
        "star_reward_eligible": payload.star_reward_eligible,
        "completed_at": completed_at.isoformat(),
    }
    attributes["growth_profile"] = growth_profile
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
    db.add(GarveySyncEvent(event_type=payload.event, external_user_id=str(payload.external_user_id), payload=_payload_json(payload), status="processed", retry_count=0))
    db.commit()
    return {"ok": True, "stored": completion, "growth_profile": growth_profile, "star_awarded": bool(activity and not duplicate), "activity_id": activity.id if activity else None}
