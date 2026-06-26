from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_permission
from app.models import MutualAidAuditLog, MutualAidConflictDisclosure, MutualAidDecision, MutualAidFund, MutualAidRequest, MutualAidRequestDocument, MutualAidRequestStatusHistory, MutualAidReview, User
from app.services.mutual_aid import DEFAULT_MUTUAL_AID_FUND_NAME

router = APIRouter(prefix="/mutual-aid", tags=["Mutual Aid"])

CATEGORIES = {"housing", "utilities", "food", "transportation", "medical", "childcare", "emergency", "other"}
URGENCIES = {"standard", "urgent", "emergency"}
SUPPORT_METHODS = {"direct_vendor", "member_follow_up", "resource_referral", "community_follow_up", "other"}
DECISIONS = {"approve", "partial_approve", "not_approved", "close"}
DECISION_REASON_CODES = {"eligible_need", "partial_need", "insufficient_documentation", "outside_policy", "duplicate_request", "withdrawn", "unable_to_contact", "closed_by_admin", "other"}
DECISION_STATUS = {"approve": "approved", "partial_approve": "partially_approved", "not_approved": "not_approved", "close": "closed"}

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


def _audit(db, actor_id, entity_id, action, before=None, after=None):
    db.add(MutualAidAuditLog(actor_user_id=actor_id, entity_type="mutual_aid_request", entity_id=entity_id, action=action, before=before or {}, after=after or {}))


def _serialize_history(row: MutualAidRequestStatusHistory):
    return {"id": row.id, "from_status": row.from_status, "to_status": row.to_status, "changed_by_user_id": row.changed_by_user_id, "reason": row.reason, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_review(row: MutualAidReview):
    return {"id": row.id, "request_id": row.request_id, "reviewer_user_id": row.reviewer_user_id, "status": row.status, "notes": row.notes, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_conflict(row: MutualAidConflictDisclosure):
    return {"id": row.id, "request_id": row.request_id, "committee_member_id": row.committee_member_id, "disclosure": row.disclosure, "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_decision(row: MutualAidDecision):
    return {"id": row.id, "request_id": row.request_id, "decision": row.decision, "decided_by_user_id": row.decided_by_user_id, "approved_amount": row.amount_approved, "reason_code": row.reason_code, "notes": row.rationale, "appeal_eligible": row.appeal_eligible, "appeal_deadline": row.appeal_deadline.isoformat() if row.appeal_deadline else None, "appeal_instructions": row.appeal_instructions, "created_at": row.created_at.isoformat() if row.created_at else None}

def _is_admin(db, user):
    return user_has_permission(db, user, "mutual_aid:read_requests_admin")

def _assigned_review(db, request_id, user_id):
    return db.query(MutualAidReview).filter(MutualAidReview.request_id == request_id, MutualAidReview.reviewer_user_id == user_id).order_by(MutualAidReview.created_at.desc()).first()

def _ensure_reviewer_access(db, req, current_user):
    if _is_admin(db, current_user):
        return
    if not _assigned_review(db, req.id, current_user.id):
        raise HTTPException(status_code=404, detail="Request not found")

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
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}


@router.get("/requests/{request_id}")
def get_request(request_id: int, current_user: User = Depends(require_permission("mutual_aid:read_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_user_id != current_user.id and not user_has_permission(db, current_user, "mutual_aid:read_requests_admin"):
        raise HTTPException(status_code=404, detail="Request not found")
    return {"ok": True, "request": _serialize(req)}


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
    return {"ok": True, "request": _serialize(req), "requester": _serialize_user(requester), "reviews": [_serialize_review(r) for r in reviews], "status_history": [_serialize_history(h) for h in history], "conflicts": [_serialize_conflict(c) for c in conflicts], "decisions": [_serialize_decision(d) for d in decisions], "decision_reason_codes": sorted(DECISION_REASON_CODES)}


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
