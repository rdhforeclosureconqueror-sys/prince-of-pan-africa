from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_permission
from app.models import MutualAidAuditLog, MutualAidFund, MutualAidRequest, MutualAidRequestDocument, MutualAidRequestStatusHistory, User
from app.services.mutual_aid import DEFAULT_MUTUAL_AID_FUND_NAME

router = APIRouter(prefix="/mutual-aid", tags=["Mutual Aid"])

CATEGORIES = {"housing", "utilities", "food", "transportation", "medical", "childcare", "emergency", "other"}
URGENCIES = {"standard", "urgent", "emergency"}
SUPPORT_METHODS = {"direct_vendor", "member_follow_up", "resource_referral", "community_follow_up", "other"}

class RequestPayload(BaseModel):
    category: str
    urgency: str = "standard"
    requested_amount: int = Field(ge=1, le=1000000)
    explanation: str = Field(min_length=20, max_length=5000)
    preferred_support_method: str
    policy_consent: bool

class DocumentMetadataPayload(BaseModel):
    document_type: str = Field(default="supporting", max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="", max_length=128)
    file_size: int = Field(default=0, ge=0)
    storage_key: str = Field(default="", max_length=1024)


def _ensure_enabled():
    if not settings.MUTUAL_AID_REQUESTS_ENABLED or settings.ENABLE_MUTUAL_AID_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid request intake is not enabled")


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
    _ensure_enabled()
    return {"ok": True, "requests": [_serialize(r) for r in db.query(MutualAidRequest).order_by(MutualAidRequest.created_at.desc()).all()]}


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
