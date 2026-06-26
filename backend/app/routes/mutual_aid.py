from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_permission
from app.models import MutualAidAppeal, MutualAidAuditLog, MutualAidCategoryBudget, MutualAidConflictDisclosure, MutualAidDecision, MutualAidDisbursement, MutualAidDisbursementStatusHistory, MutualAidFund, MutualAidNotification, MutualAidReconciliationReport, MutualAidRequest, MutualAidRequestDocument, MutualAidRequestStatusHistory, MutualAidReview, User
from app.services.mutual_aid import DEFAULT_MUTUAL_AID_FUND_NAME, record_mutual_aid_notification

router = APIRouter(prefix="/mutual-aid", tags=["Mutual Aid"])

CATEGORIES = {"housing", "utilities", "food", "transportation", "medical", "childcare", "emergency", "other"}
URGENCIES = {"standard", "urgent", "emergency"}
SUPPORT_METHODS = {"direct_vendor", "member_follow_up", "resource_referral", "community_follow_up", "other"}
DECISIONS = {"approve", "partial_approve", "not_approved", "close"}
DECISION_REASON_CODES = {"eligible_need", "partial_need", "insufficient_documentation", "outside_policy", "duplicate_request", "withdrawn", "unable_to_contact", "closed_by_admin", "other"}
DECISION_STATUS = {"approve": "approved", "partial_approve": "partially_approved", "not_approved": "not_approved", "close": "closed"}
DISBURSEMENT_STATUSES = {"pending", "scheduled", "paid", "failed", "cancelled", "reversed", "needs_receipt", "closed"}
APPEAL_STATUSES = {"submitted", "under_review", "more_info_requested", "approved", "denied", "closed"}

class RequestPayload(BaseModel):
    category: str
    urgency: str = "standard"
    requested_amount: int = Field(ge=1, le=1000000)
    explanation: str = Field(min_length=20, max_length=5000)
    preferred_support_method: str
    policy_consent: bool

class AssignReviewerPayload(BaseModel):
    reviewer_user_id: int

class RecommendationPayload(BaseModel):
    recommendation: str = Field(min_length=3, max_length=64)
    notes: str = Field(min_length=3, max_length=5000)

class MoreInfoPayload(BaseModel):
    message: str = Field(min_length=3, max_length=5000)

class ConflictDisclosurePayload(BaseModel):
    disclosure: str = Field(min_length=3, max_length=5000)

class DecisionPayload(BaseModel):
    decision: str
    reason_code: str
    notes: str = Field(min_length=3, max_length=5000)
    approved_amount: int = Field(default=0, ge=0, le=1000000)
    appeal_eligible: bool = False
    appeal_deadline: datetime | None = None
    appeal_instructions: str = Field(default="", max_length=5000)

class DisbursementPayload(BaseModel):
    amount: int = Field(ge=1, le=1000000)
    status: str = "pending"
    receipt_required: bool = False
    scheduled_for: datetime | None = None
    notes: str = Field(default="", max_length=5000)

class DisbursementStatusPayload(BaseModel):
    status: str
    reason: str = Field(min_length=3, max_length=5000)

class AppealPayload(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    explanation: str = Field(min_length=20, max_length=5000)

class AppealReviewPayload(BaseModel):
    status: str
    notes: str = Field(min_length=3, max_length=5000)

class DocumentMetadataPayload(BaseModel):
    document_type: str = Field(default="supporting", max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="", max_length=128)
    file_size: int = Field(default=0, ge=0)
    storage_key: str = Field(default="", max_length=1024)


def _ensure_enabled():
    if not settings.MUTUAL_AID_REQUESTS_ENABLED or settings.ENABLE_MUTUAL_AID_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid request intake is not enabled")


def _ensure_review_enabled():
    _ensure_enabled()
    if not settings.MUTUAL_AID_REVIEW_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid review workflow is not enabled")

def _ensure_decisions_enabled():
    _ensure_review_enabled()
    if not settings.MUTUAL_AID_DECISIONS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid decision workflow is not enabled")

def _ensure_appeals_enabled():
    _ensure_decisions_enabled()
    if not settings.MUTUAL_AID_APPEALS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid appeals workflow is not enabled")


def _fund(db):
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    if not fund:
        raise HTTPException(status_code=503, detail="Mutual Aid fund is not initialized")
    return fund


def _validate_payload(payload: RequestPayload):
    category = payload.category.strip().lower()
    urgency = payload.urgency.strip().lower()
    support = payload.preferred_support_method.strip().lower()
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Unsupported Mutual Aid request category")
    if urgency not in URGENCIES:
        raise HTTPException(status_code=422, detail="Unsupported Mutual Aid urgency")
    if support not in SUPPORT_METHODS:
        raise HTTPException(status_code=422, detail="Unsupported preferred support method")
    if not payload.policy_consent:
        raise HTTPException(status_code=422, detail="Policy consent is required")
    return category, urgency, support


def _serialize_user(user: User | None):
    if not user:
        return None
    return {"id": user.id, "email": user.email, "role": user.role}

def _serialize(req: MutualAidRequest):
    return {
        "id": req.id,
        "category": req.category,
        "urgency": req.urgency,
        "requested_amount": req.amount_requested,
        "currency": req.currency,
        "status": req.status,
        "explanation": req.narrative,
        "preferred_support_method": req.preferred_support_method,
        "policy_consent": req.policy_consent,
        "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }


def _audit(db, actor_id, entity_id, action, before=None, after=None, entity_type="mutual_aid_request"):
    db.add(MutualAidAuditLog(actor_user_id=actor_id, entity_type=entity_type, entity_id=entity_id, action=action, before=before or {}, after=after or {}))


def _serialize_history(row: MutualAidRequestStatusHistory):
    return {"id": row.id, "from_status": row.from_status, "to_status": row.to_status, "changed_by_user_id": row.changed_by_user_id, "reason": row.reason, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_review(row: MutualAidReview):
    return {"id": row.id, "request_id": row.request_id, "reviewer_user_id": row.reviewer_user_id, "status": row.status, "notes": row.notes, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_conflict(row: MutualAidConflictDisclosure):
    return {"id": row.id, "request_id": row.request_id, "committee_member_id": row.committee_member_id, "disclosure": row.disclosure, "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_decision(row: MutualAidDecision):
    return {"id": row.id, "request_id": row.request_id, "decision": row.decision, "decided_by_user_id": row.decided_by_user_id, "approved_amount": row.amount_approved, "reason_code": row.reason_code, "notes": row.rationale, "appeal_eligible": row.appeal_eligible, "appeal_deadline": row.appeal_deadline.isoformat() if row.appeal_deadline else None, "appeal_instructions": row.appeal_instructions, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_appeal(row: MutualAidAppeal):
    return {"id": row.id, "request_id": row.request_id, "decision_id": row.decision_id, "appellant_user_id": row.appellant_user_id, "status": row.status, "reason": row.reason, "explanation": row.explanation, "reviewed_by_user_id": row.reviewed_by_user_id, "review_notes": row.review_notes, "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None, "closed_at": row.closed_at.isoformat() if row.closed_at else None, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}

def _serialize_notification(row: MutualAidNotification):
    return {"id": row.id, "request_id": row.request_id, "disbursement_id": row.disbursement_id, "recipient_user_id": row.recipient_user_id, "actor_user_id": row.actor_user_id, "audience": row.audience, "event_type": row.event_type, "title": row.title, "message": row.message, "delivery_status": row.delivery_status, "channels": row.channels, "payload": row.payload, "created_at": row.created_at.isoformat() if row.created_at else None}

def _request_notifications(db, request_id):
    return db.query(MutualAidNotification).filter(MutualAidNotification.request_id == request_id).order_by(MutualAidNotification.created_at.desc()).all()

def _request_appeals(db, request_id):
    return db.query(MutualAidAppeal).filter(MutualAidAppeal.request_id == request_id).order_by(MutualAidAppeal.created_at.desc()).all()

def _latest_not_approved_decision(db, request_id):
    return db.query(MutualAidDecision).filter(MutualAidDecision.request_id == request_id, MutualAidDecision.decision == "not_approved").order_by(MutualAidDecision.created_at.desc()).first()

def _is_admin(db, user):
    return user_has_permission(db, user, "mutual_aid:read_requests_admin")

def _assigned_review(db, request_id, user_id):
    return db.query(MutualAidReview).filter(MutualAidReview.request_id == request_id, MutualAidReview.reviewer_user_id == user_id).order_by(MutualAidReview.created_at.desc()).first()

def _ensure_reviewer_access(db, req, current_user):
    if _is_admin(db, current_user):
        return
    if not _assigned_review(db, req.id, current_user.id):
        raise HTTPException(status_code=404, detail="Request not found")

def _ensure_financial_controls_enabled():
    _ensure_decisions_enabled()
    if not settings.MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED or settings.ENABLE_MUTUAL_AID_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid financial controls are not enabled")

def _ensure_disbursement_tracking_enabled():
    _ensure_financial_controls_enabled()
    if not settings.MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid disbursement tracking is not enabled")

def _latest_approval(db, request_id):
    return db.query(MutualAidDecision).filter(MutualAidDecision.request_id == request_id, MutualAidDecision.decision.in_(["approve", "partial_approve"])).order_by(MutualAidDecision.created_at.desc()).first()

def _disbursed_total(db, request_id):
    rows = db.query(MutualAidDisbursement).filter(MutualAidDisbursement.request_id == request_id, MutualAidDisbursement.status.notin_(["cancelled", "reversed", "failed"])).all()
    return sum(row.amount for row in rows)

def _serialize_disbursement(row: MutualAidDisbursement):
    return {"id": row.id, "request_id": row.request_id, "recipient_user_id": row.recipient_user_id, "amount": row.amount, "currency": row.currency, "status": row.status, "receipt_required": row.receipt_required, "scheduled_for": row.scheduled_for.isoformat() if row.scheduled_for else None, "notes": row.notes, "created_by_user_id": row.created_by_user_id, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}

def _fund_balance_read_model(db, fund):
    active = db.query(MutualAidDisbursement).join(MutualAidRequest, MutualAidRequest.id == MutualAidDisbursement.request_id).filter(MutualAidRequest.fund_id == fund.id, MutualAidDisbursement.status.in_(["pending", "scheduled", "needs_receipt"])).all()
    paid = db.query(MutualAidDisbursement).join(MutualAidRequest, MutualAidRequest.id == MutualAidDisbursement.request_id).filter(MutualAidRequest.fund_id == fund.id, MutualAidDisbursement.status.in_(["paid", "closed"])).all()
    reserved = sum(row.amount for row in active)
    paid_total = sum(row.amount for row in paid)
    reserve_floor = fund.current_balance * fund.reserve_percent // 100
    return {"fund_id": fund.id, "current_balance": fund.current_balance, "reserved_balance": reserved, "paid_total": paid_total, "reserve_percent": fund.reserve_percent, "reserve_floor": reserve_floor, "available_for_disbursement": max(fund.current_balance - reserve_floor - reserved, 0), "approval_threshold": fund.approval_threshold, "currency": fund.currency}

def _has_open_conflict(db, request_id, reviewer_id):
    review = _assigned_review(db, request_id, reviewer_id)
    if not review:
        return False
    return db.query(MutualAidConflictDisclosure).filter(MutualAidConflictDisclosure.request_id == request_id, MutualAidConflictDisclosure.committee_member_id == review.id, MutualAidConflictDisclosure.status == "open").first() is not None


@router.post("/requests/draft")
def create_draft(payload: RequestPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    category, urgency, support = _validate_payload(payload)
    req = MutualAidRequest(fund_id=_fund(db).id, requester_user_id=current_user.id, category=category, urgency=urgency, amount_requested=payload.requested_amount, narrative=payload.explanation.strip(), preferred_support_method=support, policy_consent=True, status="draft")
    db.add(req); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=None, to_status="draft", changed_by_user_id=current_user.id, reason="member draft saved"))
    _audit(db, current_user.id, req.id, "draft_saved", after=_serialize(req))
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}


@router.post("/requests/{request_id}/submit")
def submit_request(request_id: int, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "draft": raise HTTPException(status_code=409, detail="Only draft requests can be submitted")
    before = _serialize(req); req.status = "submitted"; req.submitted_at = datetime.utcnow()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status="draft", to_status="submitted", changed_by_user_id=current_user.id, reason="member submitted request"))
    _audit(db, current_user.id, req.id, "submitted", before=before, after=_serialize(req)); _audit(db, current_user.id, req.id, "status_changed", before={"status":"draft"}, after={"status":"submitted"})
    record_mutual_aid_notification(db, event_type="request_submitted", request_id=req.id, recipient_user_id=current_user.id, actor_user_id=current_user.id, payload={"status": "submitted"})
    record_mutual_aid_notification(db, event_type="admin_request_submitted", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"requester_user_id": current_user.id, "status": "submitted"})
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}


@router.get("/requests/{request_id}")
def get_request(request_id: int, current_user: User = Depends(require_permission("mutual_aid:read_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_user_id != current_user.id and not user_has_permission(db, current_user, "mutual_aid:read_requests_admin"):
        raise HTTPException(status_code=404, detail="Request not found")
    notifications = db.query(MutualAidNotification).filter(MutualAidNotification.request_id == req.id, MutualAidNotification.recipient_user_id == current_user.id).order_by(MutualAidNotification.created_at.desc()).all()
    appeals = _request_appeals(db, req.id)
    return {"ok": True, "request": _serialize(req), "appeals": [_serialize_appeal(a) for a in appeals], "notifications": [_serialize_notification(n) for n in notifications]}


@router.get("/admin/requests")
def admin_requests(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    return {"ok": True, "requests": [_serialize(r) for r in db.query(MutualAidRequest).order_by(MutualAidRequest.created_at.desc()).all()]}



@router.get("/admin/requests/{request_id}")
def admin_request_detail(request_id: int, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    reviews = db.query(MutualAidReview).filter(MutualAidReview.request_id == req.id).order_by(MutualAidReview.created_at.desc()).all()
    history = db.query(MutualAidRequestStatusHistory).filter(MutualAidRequestStatusHistory.request_id == req.id).order_by(MutualAidRequestStatusHistory.created_at.desc()).all()
    conflicts = db.query(MutualAidConflictDisclosure).filter(MutualAidConflictDisclosure.request_id == req.id).order_by(MutualAidConflictDisclosure.created_at.desc()).all()
    decisions = db.query(MutualAidDecision).filter(MutualAidDecision.request_id == req.id).order_by(MutualAidDecision.created_at.desc()).all()
    requester = db.query(User).filter(User.id == req.requester_user_id).first() if req.requester_user_id else None
    notifications = _request_notifications(db, req.id)
    appeals = _request_appeals(db, req.id)
    return {"ok": True, "request": _serialize(req), "requester": _serialize_user(requester), "reviews": [_serialize_review(r) for r in reviews], "status_history": [_serialize_history(h) for h in history], "conflicts": [_serialize_conflict(c) for c in conflicts], "decisions": [_serialize_decision(d) for d in decisions], "appeals": [_serialize_appeal(a) for a in appeals], "notifications": [_serialize_notification(n) for n in notifications], "decision_reason_codes": sorted(DECISION_REASON_CODES), "appeal_statuses": sorted(APPEAL_STATUSES)}


@router.post("/admin/requests/{request_id}/decision")
def record_decision(request_id: int, payload: DecisionPayload, current_user: User = Depends(require_permission("mutual_aid:decide_requests")), db: Session = Depends(get_db)):
    _ensure_decisions_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    decision_value = payload.decision.strip().lower()
    reason_code = payload.reason_code.strip().lower()
    if decision_value not in DECISIONS: raise HTTPException(status_code=422, detail="Unsupported Mutual Aid decision")
    if reason_code not in DECISION_REASON_CODES: raise HTTPException(status_code=422, detail="Unsupported Mutual Aid decision reason code")
    if decision_value in {"approve", "partial_approve"} and payload.approved_amount <= 0: raise HTTPException(status_code=422, detail="Approved decisions require an approved amount")
    if decision_value in {"not_approved", "close"} and payload.approved_amount != 0: raise HTTPException(status_code=422, detail="Non-approval decisions cannot record an approved amount")
    if _has_open_conflict(db, req.id, current_user.id): raise HTTPException(status_code=409, detail="Conflicted reviewers cannot decide")
    before = _serialize(req)
    next_status = DECISION_STATUS[decision_value]
    decision = MutualAidDecision(request_id=req.id, decision=decision_value, decided_by_user_id=current_user.id, amount_approved=payload.approved_amount, reason_code=reason_code, rationale=payload.notes.strip(), appeal_eligible=payload.appeal_eligible, appeal_deadline=payload.appeal_deadline, appeal_instructions=payload.appeal_instructions.strip())
    req.status = next_status
    db.add(decision); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=next_status, changed_by_user_id=current_user.id, reason=f"decision:{decision_value}:{reason_code}"))
    _audit(db, current_user.id, req.id, "decision_recorded", before=before, after={"request": _serialize(req), "decision": _serialize_decision(decision)})
    record_mutual_aid_notification(db, event_type="decision_recorded", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"decision": decision_value, "status": next_status, "appeal_eligible": payload.appeal_eligible})
    record_mutual_aid_notification(db, event_type="admin_decision_recorded", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"decision": decision_value, "status": next_status})
    if payload.appeal_eligible:
        record_mutual_aid_notification(db, event_type="appeal_window_reminder", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"appeal_deadline": payload.appeal_deadline.isoformat() if payload.appeal_deadline else None})
    _audit(db, current_user.id, req.id, "status_changed", before={"status": before["status"]}, after={"status": next_status})
    db.commit(); db.refresh(decision); db.refresh(req)
    return {"ok": True, "request": _serialize(req), "decision": _serialize_decision(decision)}

@router.post("/admin/requests/{request_id}/assign-reviewer")
def assign_reviewer(request_id: int, payload: AssignReviewerPayload, current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    reviewer = db.query(User).filter(User.id == payload.reviewer_user_id).first()
    if not req or not reviewer: raise HTTPException(status_code=404, detail="Request not found")
    review = MutualAidReview(request_id=req.id, reviewer_user_id=reviewer.id, status="assigned", notes="")
    before = {"status": req.status}; req.status = "under_review"
    db.add(review); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=req.status, changed_by_user_id=current_user.id, reason=f"reviewer assigned: {reviewer.id}"))
    _audit(db, current_user.id, req.id, "reviewer_assigned", before=before, after={"status": req.status, "reviewer_user_id": reviewer.id, "review_id": review.id})
    db.commit(); db.refresh(review)
    return {"ok": True, "review": _serialize_review(review), "request": _serialize(req)}

@router.post("/admin/requests/{request_id}/recommendation")
def reviewer_recommendation(request_id: int, payload: RecommendationPayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    if _has_open_conflict(db, req.id, current_user.id): raise HTTPException(status_code=409, detail="Conflicted reviewers cannot recommend")
    review = _assigned_review(db, req.id, current_user.id) or MutualAidReview(request_id=req.id, reviewer_user_id=current_user.id)
    before = _serialize_review(review) if review.id else {}
    review.status = f"recommended_{payload.recommendation.strip().lower()}"; review.notes = payload.notes.strip()
    db.add(review); db.flush()
    _audit(db, current_user.id, req.id, "recommendation_recorded", before=before, after=_serialize_review(review))
    db.commit(); db.refresh(review)
    return {"ok": True, "review": _serialize_review(review)}

@router.post("/admin/requests/{request_id}/request-more-info")
def request_more_info(request_id: int, payload: MoreInfoPayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    before = {"status": req.status}; req.status = "more_info_requested"
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=req.status, changed_by_user_id=current_user.id, reason=payload.message.strip()))
    _audit(db, current_user.id, req.id, "more_info_requested", before=before, after={"status": req.status, "message": payload.message.strip()})
    record_mutual_aid_notification(db, event_type="more_information_requested", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": req.status, "message": payload.message.strip()})
    record_mutual_aid_notification(db, event_type="admin_more_information_requested", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": req.status})
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}

@router.post("/admin/requests/{request_id}/conflict-disclosure")
def disclose_conflict(request_id: int, payload: ConflictDisclosurePayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    review = _assigned_review(db, req.id, current_user.id)
    if not review: raise HTTPException(status_code=404, detail="Assigned review not found")
    conflict = MutualAidConflictDisclosure(request_id=req.id, committee_member_id=review.id, disclosure=payload.disclosure.strip(), status="open")
    db.add(conflict); db.flush()
    _audit(db, current_user.id, req.id, "conflict_disclosed", after=_serialize_conflict(conflict))
    db.commit(); db.refresh(conflict)
    return {"ok": True, "conflict": _serialize_conflict(conflict)}

@router.post("/requests/{request_id}/appeals")
def submit_appeal(request_id: int, payload: AppealPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_appeals_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "not_approved":
        raise HTTPException(status_code=409, detail="Only not-approved requests can be appealed")
    decision = _latest_not_approved_decision(db, req.id)
    if not decision or not decision.appeal_eligible:
        raise HTTPException(status_code=409, detail="This request is not appeal eligible")
    if decision.appeal_deadline and datetime.utcnow() > decision.appeal_deadline:
        raise HTTPException(status_code=409, detail="The appeal deadline has passed")
    existing = db.query(MutualAidAppeal).filter(MutualAidAppeal.request_id == req.id, MutualAidAppeal.status.in_(["submitted", "under_review", "more_info_requested"])).first()
    if existing:
        raise HTTPException(status_code=409, detail="An open appeal already exists for this request")
    appeal = MutualAidAppeal(request_id=req.id, decision_id=decision.id, appellant_user_id=current_user.id, status="submitted", reason=payload.reason.strip(), explanation=payload.explanation.strip())
    db.add(appeal); db.flush()
    _audit(db, current_user.id, appeal.id, "appeal_submitted", after=_serialize_appeal(appeal), entity_type="mutual_aid_appeal")
    _audit(db, current_user.id, req.id, "appeal_submitted", after={"appeal": _serialize_appeal(appeal)})
    record_mutual_aid_notification(db, event_type="appeal_submitted", request_id=req.id, recipient_user_id=current_user.id, actor_user_id=current_user.id, payload={"appeal_id": appeal.id, "status": appeal.status})
    record_mutual_aid_notification(db, event_type="admin_appeal_submitted", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"appeal_id": appeal.id, "status": appeal.status})
    db.commit(); db.refresh(appeal)
    return {"ok": True, "appeal": _serialize_appeal(appeal)}

@router.post("/admin/appeals/{appeal_id}/review")
def review_appeal(appeal_id: int, payload: AppealReviewPayload, current_user: User = Depends(require_permission("mutual_aid:decide_requests")), db: Session = Depends(get_db)):
    _ensure_appeals_enabled()
    appeal = db.query(MutualAidAppeal).filter(MutualAidAppeal.id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in APPEAL_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported appeal status")
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == appeal.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    before = _serialize_appeal(appeal)
    appeal.status = normalized_status
    appeal.review_notes = payload.notes.strip()
    appeal.reviewed_by_user_id = current_user.id
    appeal.reviewed_at = datetime.utcnow()
    if normalized_status in {"approved", "denied", "closed"}:
        appeal.closed_at = appeal.reviewed_at
    _audit(db, current_user.id, appeal.id, "appeal_reviewed", before=before, after=_serialize_appeal(appeal), entity_type="mutual_aid_appeal")
    _audit(db, current_user.id, req.id, "appeal_reviewed", before={"appeal": before}, after={"appeal": _serialize_appeal(appeal)})
    record_mutual_aid_notification(db, event_type="appeal_status_changed", request_id=req.id, recipient_user_id=appeal.appellant_user_id, actor_user_id=current_user.id, payload={"appeal_id": appeal.id, "status": appeal.status})
    record_mutual_aid_notification(db, event_type="admin_appeal_status_changed", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"appeal_id": appeal.id, "status": appeal.status})
    db.commit(); db.refresh(appeal)
    return {"ok": True, "appeal": _serialize_appeal(appeal)}

@router.post("/requests/{request_id}/documents/metadata")
def document_metadata(request_id: int, payload: DocumentMetadataPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    doc = MutualAidRequestDocument(request_id=req.id, document_type=payload.document_type.strip() or "supporting", filename=payload.filename.strip(), content_type=payload.content_type.strip(), file_size=payload.file_size, storage_key=payload.storage_key.strip(), status="metadata_only")
    db.add(doc); db.flush()
    _audit(db, current_user.id, req.id, "document_metadata_added", after={"document_id": doc.id, "filename": doc.filename, "content_type": doc.content_type, "file_size": doc.file_size})
    db.commit()
    return {"ok": True, "document": {"id": doc.id, "filename": doc.filename, "status": doc.status}}


@router.get("/admin/financial-controls")
def financial_controls(current_user: User = Depends(require_permission("mutual_aid:read_financial_controls")), db: Session = Depends(get_db)):
    _ensure_financial_controls_enabled()
    fund = _fund(db)
    budgets = db.query(MutualAidCategoryBudget).filter(MutualAidCategoryBudget.fund_id == fund.id).order_by(MutualAidCategoryBudget.category.asc()).all()
    reports = db.query(MutualAidReconciliationReport).filter(MutualAidReconciliationReport.fund_id == fund.id).order_by(MutualAidReconciliationReport.created_at.desc()).all()
    return {"ok": True, "balance": _fund_balance_read_model(db, fund), "category_budgets": [{"id": b.id, "category": b.category, "budget_amount": b.budget_amount, "reserved_amount": b.reserved_amount, "currency": b.currency} for b in budgets], "reconciliation_reports": [{"id": r.id, "status": r.status, "totals": r.totals, "created_at": r.created_at.isoformat() if r.created_at else None} for r in reports]}

@router.get("/admin/disbursements")
def list_disbursements(current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    rows = db.query(MutualAidDisbursement).order_by(MutualAidDisbursement.created_at.desc()).all()
    return {"ok": True, "statuses": sorted(DISBURSEMENT_STATUSES), "disbursements": [_serialize_disbursement(row) for row in rows]}

@router.post("/admin/requests/{request_id}/disbursements")
def create_disbursement(request_id: int, payload: DisbursementPayload, current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in {"approved", "partially_approved"}: raise HTTPException(status_code=409, detail="Only approved requests can receive disbursement records")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in DISBURSEMENT_STATUSES: raise HTTPException(status_code=422, detail="Unsupported disbursement status")
    approval = _latest_approval(db, req.id)
    if not approval: raise HTTPException(status_code=409, detail="Approved request is missing an approval decision")
    if _disbursed_total(db, req.id) + payload.amount > approval.amount_approved: raise HTTPException(status_code=409, detail="Disbursement exceeds approved amount")
    fund = db.query(MutualAidFund).filter(MutualAidFund.id == req.fund_id).one()
    balance = _fund_balance_read_model(db, fund)
    if payload.amount > balance["available_for_disbursement"]: raise HTTPException(status_code=409, detail="Reserve rule blocks this disbursement record")
    if payload.amount > fund.approval_threshold and current_user.role not in {"admin", "superadmin"}: raise HTTPException(status_code=403, detail="Disbursement exceeds treasurer approval threshold")
    row = MutualAidDisbursement(request_id=req.id, recipient_user_id=req.requester_user_id, amount=payload.amount, currency=req.currency, status=normalized_status, receipt_required=payload.receipt_required, scheduled_for=payload.scheduled_for, notes=payload.notes.strip(), created_by_user_id=current_user.id)
    db.add(row); db.flush()
    db.add(MutualAidDisbursementStatusHistory(disbursement_id=row.id, from_status=None, to_status=normalized_status, changed_by_user_id=current_user.id, reason="administrative tracking record created"))
    _audit(db, current_user.id, row.id, "disbursement_record_created", after=_serialize_disbursement(row))
    record_mutual_aid_notification(db, event_type="disbursement_record_created", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status, "receipt_required": payload.receipt_required})
    record_mutual_aid_notification(db, event_type="admin_disbursement_record_created", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status, "amount": payload.amount})
    if payload.receipt_required or normalized_status == "needs_receipt":
        record_mutual_aid_notification(db, event_type="receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status})
        record_mutual_aid_notification(db, event_type="admin_receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status})
    db.commit(); db.refresh(row)
    return {"ok": True, "disbursement": _serialize_disbursement(row)}

@router.post("/admin/disbursements/{disbursement_id}/status")
def update_disbursement_status(disbursement_id: int, payload: DisbursementStatusPayload, current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    row = db.query(MutualAidDisbursement).filter(MutualAidDisbursement.id == disbursement_id).first()
    if not row: raise HTTPException(status_code=404, detail="Disbursement not found")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in DISBURSEMENT_STATUSES: raise HTTPException(status_code=422, detail="Unsupported disbursement status")
    before = _serialize_disbursement(row); old = row.status; row.status = normalized_status
    if normalized_status == "closed": row.closed_at = datetime.utcnow()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == row.request_id).first()
    if normalized_status == "needs_receipt" and req:
        record_mutual_aid_notification(db, event_type="receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status, "reason": payload.reason.strip()})
        record_mutual_aid_notification(db, event_type="admin_receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status})
    db.add(MutualAidDisbursementStatusHistory(disbursement_id=row.id, from_status=old, to_status=normalized_status, changed_by_user_id=current_user.id, reason=payload.reason.strip()))
    _audit(db, current_user.id, row.id, "disbursement_status_changed", before=before, after=_serialize_disbursement(row))
    db.commit(); db.refresh(row)
    return {"ok": True, "disbursement": _serialize_disbursement(row)}
