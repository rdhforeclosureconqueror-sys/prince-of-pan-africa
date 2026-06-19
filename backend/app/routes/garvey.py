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
from app.dependencies.auth import require_auth, require_permission
from app.models import GarveySyncEvent, MemberProfile, User
from app.routes.member import _membership_type_from_subscription
from app.services.billing import latest_subscription_for_user
from app.services.participation import find_duplicate_activity, submit_activity

router = APIRouter(prefix="/member/assessments", tags=["Garvey Assessments"])
legacy_callback_router = APIRouter(prefix="/api/simbawajuma", tags=["Garvey Assessments"])
callback_router = APIRouter(tags=["Garvey Assessments"])


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


def _sync_event_payload(payload: BaseModel | dict, *, signature_valid: bool | None = None, synced_member_email: str | None = None, error_message: str | None = None) -> dict:
    body = _payload_json(payload) if isinstance(payload, BaseModel) else dict(payload or {})
    body["sync_diagnostics"] = {
        "callback_signature_valid": signature_valid,
        "synced_member_email": synced_member_email,
        "assessment_id": body.get("assessment_id") or body.get("assessment_type") or body.get("assessment_name"),
        "error_message": error_message,
        "received_at": datetime.utcnow().isoformat(),
    }
    return body


def _serialize_sync_event(row: GarveySyncEvent | None) -> dict | None:
    if not row:
        return None
    payload = row.payload or {}
    diagnostics = payload.get("sync_diagnostics") if isinstance(payload, dict) else {}
    return {
        "id": row.id,
        "event_type": row.event_type,
        "status": row.status,
        "external_user_id": row.external_user_id,
        "retry_count": row.retry_count,
        "last_error": row.last_error,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "callback_signature_validation_status": diagnostics.get("callback_signature_valid"),
        "synced_member_email": diagnostics.get("synced_member_email"),
        "assessment_id": diagnostics.get("assessment_id"),
        "error_message": diagnostics.get("error_message") or row.last_error,
    }


def _display_name(user: User, profile: MemberProfile | None) -> str:
    attrs = profile.attributes if profile else {}
    for key in ("display_name", "name", "first_name"):
        if attrs.get(key):
            return str(attrs[key])
    return (user.email or "Member").split("@", 1)[0].replace(".", " ").replace("_", " ").title()


class TransferTokenPayload(BaseModel):
    redirect_assessment: str | None = Field(default=None, max_length=160)
    destination: str | None = Field(default="assessment", max_length=80)


class GarveyCompletionPayload(BaseModel):
    event: str = "assessment.completed"
    issuer: str | None = None
    external_user_id: str | int | None = Field(default=None, alias="member_id")
    member_email: str | None = None
    email: str | None = None
    external_membership_id: str | int | None = None
    assessment_type: str | None = None
    assessment_id: str | int | None = None
    assessment_name: str | None = None
    result_id: str | int | None = None
    completion_status: str = "completed"
    overall_score: float | None = None
    percentile: float | None = None
    strengths: list[str] = Field(default_factory=list)
    opportunities_for_growth: list[str] = Field(default_factory=list)
    recommended_next_assessment: str | dict | None = None
    recommendation_confidence: float | None = None
    primary_result: dict | str | None = None
    recommended_next_steps: list | dict | str | None = None
    recommendations: list | dict | str | None = None
    result_summary: dict | str | None = None
    result_url: str | None = None
    archetype: dict | str | None = None
    star_reward_eligible: bool = False
    completed_at: datetime | None = None

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True
        extra = "allow"


def _string_or_none(value: str | int | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _normalize_garvey_payload_ids(payload: GarveyCompletionPayload) -> GarveyCompletionPayload:
    payload.result_id = _string_or_none(payload.result_id)
    payload.assessment_id = _string_or_none(payload.assessment_id)
    return payload


def _payload_json(payload: BaseModel) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json")
    return json.loads(payload.json())


OFFICIAL_ASSESSMENTS = [
    {"key": "business-owner-assessment", "title": "Business Owner Assessment", "aliases": ["business-assessment", "business-owner"]},
    {"key": "customer-voice-of-customer", "title": "Customer / Voice of Customer", "aliases": ["voice-of-customer", "customer-assessment", "voc"]},
    {"key": "love-archetype-engine", "title": "Love Archetype Engine", "aliases": ["love-engine", "love-archetype"]},
    {"key": "leadership-archetype-engine", "title": "Leadership Archetype Engine", "aliases": ["leadership-engine", "leadership-archetype"]},
    {"key": "loyalty-archetype-engine", "title": "Loyalty Archetype Engine", "aliases": ["loyalty-engine", "loyalty-archetype"]},
    {"key": "youth-rite-of-passage", "title": "Youth Rite of Passage / Gates", "aliases": ["rite-of-passage", "gates"]},
    {"key": "k-6-assessment-mvp", "title": "K–6 Assessment MVP", "aliases": ["k6-assessment-mvp", "k-6", "k6"]},
]

GROWTH_CATEGORIES = [item["title"] for item in OFFICIAL_ASSESSMENTS]

BADGE_RULES = [
    ("first_assessment", "First Assessment", lambda profile: profile["summary"]["completed_assessments"] >= 1),
    ("lifelong_learner", "Lifelong Learner", lambda profile: profile["summary"]["total_attempts"] >= 3),
]


def _category_from_payload(payload: GarveyCompletionPayload) -> str:
    raw = (payload.assessment_type or payload.assessment_id or payload.assessment_name or "").replace("_", " ").replace("-", " ").lower()
    if "business" in raw or "owner" in raw:
        return "Business Owner Assessment"
    if "customer" in raw or "voice of customer" in raw or "voc" in raw:
        return "Customer / Voice of Customer"
    if "love" in raw:
        return "Love Archetype Engine"
    if "leadership" in raw:
        return "Leadership Archetype Engine"
    if "loyalty" in raw:
        return "Loyalty Archetype Engine"
    if "rite" in raw or "passage" in raw or "gate" in raw:
        return "Youth Rite of Passage / Gates"
    if "k 6" in raw or "k6" in raw or "elementary" in raw:
        return "K–6 Assessment MVP"
    return payload.assessment_name or payload.assessment_type or payload.assessment_id or "Garvey Assessment"


def _blank_growth_profile() -> dict:
    return {"categories": {name: {"assessments": {}, "latest_score": None, "status": "not_started"} for name in GROWTH_CATEGORIES}, "badges": [], "timeline": [], "summary": {"overall_completion": 0, "completed_assessments": 0, "total_attempts": 0}}


def _category_score(profile: dict, category: str) -> float:
    return float(profile.get("categories", {}).get(category, {}).get("latest_score") or 0)


def _category_attempts(profile: dict, category: str) -> int:
    return sum(int(item.get("attempts") or 0) for item in profile.get("categories", {}).get(category, {}).get("assessments", {}).values())


def _recommended_review_date(completed_at: datetime) -> str:
    return (completed_at + timedelta(days=90)).date().isoformat()


def _next_assessment(profile: dict, fallback: str | dict | None) -> dict:
    if fallback:
        if isinstance(fallback, dict):
            name = fallback.get("assessment_name") or fallback.get("name") or fallback.get("title") or fallback.get("key") or "Recommended Garvey assessment"
            return {**fallback, "assessment_name": name, "confidence": fallback.get("confidence"), "reason": fallback.get("reason") or "Garvey recommended this from the latest result."}
        return {"assessment_name": fallback, "confidence": None, "reason": "Garvey recommended this from the latest result."}
    attempted = {name for name in GROWTH_CATEGORIES if _category_attempts(profile, name)}
    next_item = next((item for item in OFFICIAL_ASSESSMENTS if item["title"] not in attempted), OFFICIAL_ASSESSMENTS[0])
    return {"assessment_name": next_item["title"], "confidence": 0.65, "reason": "Continue with the next official active assessment."}


def _apply_assessment_completion(profile: dict, payload: GarveyCompletionPayload, completed_at: datetime) -> tuple[dict, dict]:
    growth = dict(profile or _blank_growth_profile())
    growth.setdefault("categories", _blank_growth_profile()["categories"])
    growth.setdefault("timeline", [])
    growth.setdefault("badges", [])
    category = _category_from_payload(payload)
    cat = growth["categories"].setdefault(category, {"assessments": {}, "latest_score": None, "status": "not_started"})
    assessments = cat.setdefault("assessments", {})
    assessment_name = payload.assessment_name or payload.assessment_type or payload.assessment_id or "Garvey Assessment"
    assessment_id = payload.assessment_id or payload.assessment_type or assessment_name
    current = assessments.get(assessment_id, {})
    score = payload.overall_score
    attempts = int(current.get("attempts") or 0) + 1
    record = {**current, "assessment_id": assessment_id, "assessment_name": assessment_name, "latest_score": score, "highest_score": max([v for v in [current.get("highest_score"), score] if v is not None], default=None), "completion_date": completed_at.isoformat(), "attempts": attempts, "completion_status": payload.completion_status, "recommended_review_date": _recommended_review_date(completed_at), "percentile": payload.percentile, "strengths": payload.strengths, "opportunities_for_growth": payload.opportunities_for_growth}
    assessments[assessment_id] = record
    cat["latest_score"] = score
    cat["status"] = payload.completion_status
    recommendation = _next_assessment(growth, payload.recommended_next_assessment)
    if payload.recommendation_confidence is not None:
        recommendation["confidence"] = payload.recommendation_confidence
    record["recommended_next_assessment"] = recommendation
    growth["timeline"] = [{"assessment_id": assessment_id, "assessment_name": assessment_name, "category": category, "score": score, "status": payload.completion_status, "completed_at": completed_at.isoformat()}, *[i for i in growth.get("timeline", []) if i.get("result_id") != payload.result_id]][:100]
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
    return _filter_official_catalog(response.json())


def _catalog_items(payload: dict | list) -> list:
    if isinstance(payload, list):
        return payload
    for key in ("assessments", "items", "data", "catalog"):
        if isinstance(payload, dict) and isinstance(payload.get(key), list):
            return payload[key]
    return []


def _assessment_slug(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace("/", " ").replace("–", "-").replace(" ", "-")


def _is_official_assessment(item: dict) -> bool:
    raw = " ".join(str(item.get(key, "")) for key in ("id", "slug", "key", "assessment_type", "type", "name", "title", "assessment_name"))
    normalized = _assessment_slug(raw)
    return any(
        official["key"] in normalized
        or _assessment_slug(official["title"]) in normalized
        or any(_assessment_slug(alias) in normalized for alias in official.get("aliases", []))
        for official in OFFICIAL_ASSESSMENTS
    )


def _assessment_group_key(item: dict) -> str:
    raw_values = [
        item.get("assessment_id"),
        item.get("assessment_type"),
        item.get("assessment_name"),
        item.get("category"),
        item.get("slug"),
        item.get("id"),
    ]
    raw = " ".join(str(value) for value in raw_values if value).replace("_", " ").replace("-", " ").lower()
    for official in OFFICIAL_ASSESSMENTS:
        terms = [official["key"], official["title"], *official.get("aliases", [])]
        normalized_terms = [term.replace("_", " ").replace("-", " ").lower() for term in terms]
        if any(term and term in raw for term in normalized_terms):
            return official["key"]
    fallback = item.get("assessment_id") or item.get("assessment_type") or item.get("assessment_name") or item.get("category") or "garvey-assessment"
    return _assessment_slug(str(fallback))


def _completion_timestamp(item: dict) -> str:
    return str(item.get("completed_at") or item.get("completion_date") or item.get("created_at") or "")


def _completion_sort_key(item: dict) -> tuple[str, str]:
    return (_completion_timestamp(item), str(item.get("result_id") or item.get("assessment_id") or ""))


def _group_assessment_attempts(completions: list[dict]) -> tuple[list[dict], dict]:
    grouped: dict[str, list[dict]] = {}
    for completion in completions:
        if not isinstance(completion, dict):
            continue
        grouped.setdefault(_assessment_group_key(completion), []).append(completion)

    latest_results = []
    attempt_history = {}
    for key, attempts in grouped.items():
        sorted_attempts = sorted(attempts, key=_completion_sort_key, reverse=True)
        latest = dict(sorted_attempts[0])
        latest["assessment_group_key"] = key
        latest["attempt_count"] = len(sorted_attempts)
        latest["attempt_history"] = sorted_attempts
        latest_results.append(latest)
        attempt_history[key] = sorted_attempts

    latest_results.sort(key=_completion_sort_key, reverse=True)
    return latest_results, attempt_history


def _filter_official_catalog(payload: dict | list) -> dict | list:
    items = [item for item in _catalog_items(payload) if isinstance(item, dict) and _is_official_assessment(item)]
    if isinstance(payload, list):
        return items
    cleaned = dict(payload or {})
    target_key = next((key for key in ("assessments", "items", "data", "catalog") if isinstance(cleaned.get(key), list)), "assessments")
    cleaned[target_key] = items
    return cleaned


def _official_assessment_key(raw: str) -> str:
    normalized = raw.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "youth-rite-of-passage": "youth-rite-of-passage",
        "rite-of-passage": "youth-rite-of-passage",
        "k-6-assessment-mvp": "k-6-assessment-mvp",
        "k6-assessment-mvp": "k-6-assessment-mvp",
        "k-6": "k-6-assessment-mvp",
    }
    return aliases.get(normalized, raw)


@router.get("/archetypes")
def get_archetype_catalog(current_user: User = Depends(require_auth)):
    base = _configured_garvey_base()
    del current_user
    errors: list[str] = []
    for path in ("api/simbawajuma/archetypes", "api/simbawajuma/assessment-archetypes"):
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(urljoin(f"{base}/", path))
                if response.status_code == 404:
                    errors.append(f"{path}: 404")
                    continue
                response.raise_for_status()
                payload = response.json()
                return {"ok": True, "source": path, "base_url": base, "catalog": payload}
        except httpx.HTTPError as exc:
            errors.append(f"{path}: {exc}")
    return {"ok": False, "source": None, "base_url": base, "catalog": [], "detail": "Garvey archetype catalog is unavailable; Simba will hide archetype links instead of guessing.", "errors": errors}


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
        "return_url": "https://simbawaujamaa.com/dashboard",
        "result_return_url": "https://simbawaujamaa.com/dashboard",
        "dashboard_url": "https://simbawaujamaa.com/dashboard",
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    if payload.redirect_assessment:
        token_payload["redirect_assessment"] = _official_assessment_key(payload.redirect_assessment)
    return {"ok": True, "token": _sign(token_payload, settings.GARVEY_TRANSFER_SECRET), "start_url": f"{base}/simbawajuma/start", "return_url": "https://simbawaujamaa.com/dashboard"}


@router.get("/results")
def get_assessment_results(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = _member_profile(db, current_user)
    attributes = profile.attributes or {}
    completions = list(attributes.get("garvey_assessment_completions", []))
    latest_results, attempt_history = _group_assessment_attempts(completions)
    return {
        "ok": True,
        "results": completions,
        "latest_results": latest_results,
        "attempt_history": attempt_history,
        "growth_profile": attributes.get("growth_profile", _blank_growth_profile()),
    }


@router.get("/results/{result_id}")
def get_assessment_result(result_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = _member_profile(db, current_user)
    completions = list((profile.attributes or {}).get("garvey_assessment_completions", []))
    for completion in completions:
        if str(completion.get("result_id") or completion.get("assessment_id")) == result_id:
            return {"ok": True, "result": completion}
    raise HTTPException(status_code=404, detail="Assessment result not found.")


@router.get("/sync-diagnostics")
def get_garvey_sync_diagnostics(_: User = Depends(require_permission("admin:read_dashboard")), db: Session = Depends(get_db)):
    required_env = ["GARVEY_BASE_URL", "GARVEY_TRANSFER_SECRET", "GARVEY_ALLOWED_ISSUER", "GARVEY_CALLBACK_SECRET"]
    env = {name: {"present": bool(getattr(settings, name, "").strip()), "configured_name": name} for name in required_env}
    latest = db.query(GarveySyncEvent).order_by(GarveySyncEvent.created_at.desc(), GarveySyncEvent.id.desc()).first()
    successful = db.query(GarveySyncEvent).filter(GarveySyncEvent.status == "processed").order_by(GarveySyncEvent.updated_at.desc(), GarveySyncEvent.id.desc()).first()
    failed = db.query(GarveySyncEvent).filter(GarveySyncEvent.status.in_(["failed", "pending"])).order_by(GarveySyncEvent.updated_at.desc(), GarveySyncEvent.id.desc()).first()
    return {"ok": True, "required_env": env, "last_callback_received": _serialize_sync_event(latest), "last_successful_assessment_sync": _serialize_sync_event(successful), "last_failed_assessment_sync": _serialize_sync_event(failed)}


@router.get("/growth-profile")
def get_growth_profile(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = _member_profile(db, current_user)
    return {"ok": True, "growth_profile": (profile.attributes or {}).get("growth_profile", _blank_growth_profile())}


def _process_garvey_assessment_callback(
    payload: GarveyCompletionPayload,
    x_garvey_callback_secret: str | None = Header(default=None, alias="X-Garvey-Callback-Secret"),
    authorization: str | None = Header(default=None),
    x_garvey_signature: str | None = None,
    x_garvey_timestamp: str | None = None,
    db: Session = Depends(get_db),
):
    payload = _normalize_garvey_payload_ids(payload)
    expected_secret = settings.GARVEY_CALLBACK_SECRET.strip()
    bearer = authorization.removeprefix("Bearer ").strip() if authorization else None
    if not expected_secret or not hmac.compare_digest(x_garvey_callback_secret or bearer or "", expected_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Garvey callback secret")
    if payload.event not in {"assessment.completed", "assessment.result.completed", "completed", "assessment_completion"}:
        raise HTTPException(status_code=400, detail="Unsupported Garvey assessment event")
    if settings.GARVEY_ALLOWED_ISSUER and payload.issuer and payload.issuer != settings.GARVEY_ALLOWED_ISSUER:
        raise HTTPException(status_code=403, detail="Unsupported Garvey issuer")

    user = None
    if payload.external_user_id is not None:
        try:
            simba_user_id = int(payload.external_user_id)
        except (TypeError, ValueError):
            simba_user_id = None
        if simba_user_id is not None:
            user = db.query(User).filter(User.id == simba_user_id).first()
    callback_email = (payload.member_email or payload.email or "").strip().lower()
    if not user and callback_email:
        user = db.query(User).filter(User.email == callback_email).first()
    external_id = str(payload.external_user_id or callback_email or "unknown")
    if not user:
        db.add(GarveySyncEvent(event_type=payload.event, external_user_id=external_id, payload=_sync_event_payload(payload, signature_valid=True, error_message="Simba member not found"), status="pending", retry_count=0, last_error="Simba member not found"))
        db.commit()
        return {"ok": False, "queued": True, "detail": "Simba member not found; queued for retry"}
    profile = _member_profile(db, user)
    completed_at = payload.completed_at or datetime.utcnow()
    assessment_name = payload.assessment_name or payload.assessment_type or payload.assessment_id or "Garvey Assessment"
    recommended_steps = payload.recommended_next_steps if payload.recommended_next_steps is not None else payload.recommendations
    attributes = dict(profile.attributes or {})
    growth_profile, assessment_record = _apply_assessment_completion(attributes.get("growth_profile", _blank_growth_profile()), payload, completed_at)
    completion = {
        "assessment_type": payload.assessment_type or _category_from_payload(payload).lower().replace(" ", "_"),
        "category": _category_from_payload(payload),
        "assessment_id": payload.assessment_id or payload.assessment_type or assessment_name,
        "assessment_name": assessment_name,
        "result_id": payload.result_id or payload.assessment_id or assessment_name,
        "completion_status": payload.completion_status,
        "overall_score": payload.overall_score,
        "percentile": payload.percentile,
        "strengths": payload.strengths,
        "opportunities_for_growth": payload.opportunities_for_growth,
        "recommended_next_assessment": assessment_record.get("recommended_next_assessment"),
        "primary_result": payload.primary_result,
        "recommended_next_steps": recommended_steps,
        "recommendations": payload.recommendations,
        "result_summary": payload.result_summary,
        "result_url": payload.result_url,
        "archetype": payload.archetype,
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
    event_payload = _sync_event_payload(payload, signature_valid=True, synced_member_email=user.email)
    event_payload["sync_diagnostics"]["garvey_signature_header_present"] = bool(x_garvey_signature)
    event_payload["sync_diagnostics"]["garvey_timestamp_header_present"] = bool(x_garvey_timestamp)
    missing = [key for key, value in {"member_email": callback_email, "result_id": payload.result_id, "result_url": payload.result_url, "assessment_id": payload.assessment_id}.items() if not value]
    event_payload["sync_diagnostics"]["missing_optional_fields"] = missing
    db.add(GarveySyncEvent(event_type=payload.event, external_user_id=external_id, payload=event_payload, status="processed", retry_count=0))
    db.commit()
    return {"ok": True, "stored": completion, "growth_profile": growth_profile, "star_awarded": bool(activity and not duplicate), "activity_id": activity.id if activity else None}


@legacy_callback_router.post("/assessment-callback")
def garvey_legacy_assessment_callback(payload: GarveyCompletionPayload, x_garvey_callback_secret: str | None = Header(default=None, alias="X-Garvey-Callback-Secret"), authorization: str | None = Header(default=None), x_garvey_signature: str | None = Header(default=None, alias="X-Garvey-Signature"), x_garvey_timestamp: str | None = Header(default=None, alias="X-Garvey-Timestamp"), db: Session = Depends(get_db)):
    return _process_garvey_assessment_callback(payload, x_garvey_callback_secret, authorization, x_garvey_signature, x_garvey_timestamp, db)


@callback_router.get("/garvey/callback")
def garvey_callback_status():
    return {"ok": True, "route": "/garvey/callback", "method": "POST", "configured": bool(settings.GARVEY_CALLBACK_SECRET.strip())}


@callback_router.get("/api/garvey/callback")
def api_garvey_callback_status():
    return {"ok": True, "route": "/api/garvey/callback", "method": "POST", "configured": bool(settings.GARVEY_CALLBACK_SECRET.strip())}


@callback_router.post("/garvey/callback")
def garvey_callback(payload: GarveyCompletionPayload, x_garvey_callback_secret: str | None = Header(default=None, alias="X-Garvey-Callback-Secret"), authorization: str | None = Header(default=None), x_garvey_signature: str | None = Header(default=None, alias="X-Garvey-Signature"), x_garvey_timestamp: str | None = Header(default=None, alias="X-Garvey-Timestamp"), db: Session = Depends(get_db)):
    return _process_garvey_assessment_callback(payload, x_garvey_callback_secret, authorization, x_garvey_signature, x_garvey_timestamp, db)


@callback_router.post("/api/garvey/callback")
def api_garvey_callback(payload: GarveyCompletionPayload, x_garvey_callback_secret: str | None = Header(default=None, alias="X-Garvey-Callback-Secret"), authorization: str | None = Header(default=None), x_garvey_signature: str | None = Header(default=None, alias="X-Garvey-Signature"), x_garvey_timestamp: str | None = Header(default=None, alias="X-Garvey-Timestamp"), db: Session = Depends(get_db)):
    return _process_garvey_assessment_callback(payload, x_garvey_callback_secret, authorization, x_garvey_signature, x_garvey_timestamp, db)
