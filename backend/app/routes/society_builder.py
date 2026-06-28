from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_auth, require_permission
from app.models import Society, SocietyBlueprintAudit, SocietyCovenant, SocietyFirstTenMember, SocietyMembership, SocietyPurpose, User
from app.services.society_builder import (
    DEFAULT_COVENANT,
    audit,
    blueprint_logic,
    can_manage_society,
    first_ten_summary,
    purpose_statement_and_prompt,
    require_society_builder_enabled,
    safe_society_summary,
    seed_simba_main_hub,
    stage_eligibility,
    unique_society_slug,
)

router = APIRouter(prefix="/society-builder", tags=["Society Builder"])
CHAPTER_STATUSES = {"draft", "pending_review", "approved", "changes_requested", "declined", "active", "paused", "suspended", "inactive", "independent"}
COVENANT_STATUSES = {"Draft", "Active", "Revised", "Archived"}


class SocietyPayload(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    type: str = "Custom"
    description: str = ""
    community_served: str = ""
    location: str = ""
    state: str = ""
    city: str = ""
    region: str = ""
    first_focus: str = ""
    visibility: str = "Private"
    parent_society_id: int | None = None
    root_society_id: int | None = None
    chapter_level: str = "independent_society"
    affiliation_status: str = "draft"
    geographic_scope: str = "custom"
    is_chapter: bool = False


class SocietyPatchPayload(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    community_served: str | None = None
    location: str | None = None
    state: str | None = None
    city: str | None = None
    region: str | None = None
    first_focus: str | None = None
    visibility: str | None = None
    parent_society_id: int | None = None
    root_society_id: int | None = None
    chapter_level: str | None = None
    geographic_scope: str | None = None


class BlueprintPayload(BaseModel):
    trust_score: int = Field(ge=1, le=5)
    relationships_score: int = Field(ge=1, le=5)
    mutual_aid_score: int = Field(ge=1, le=5)
    organization_score: int = Field(ge=1, le=5)
    institutions_score: int = Field(ge=1, le=5)
    businesses_score: int = Field(ge=1, le=5)
    property_score: int = Field(ge=1, le=5)
    community_wealth_score: int = Field(ge=1, le=5)
    political_power_score: int = Field(ge=1, le=5)
    notes: str = ""


class FirstTenPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = ""
    phone: str = ""
    relationship_to_society: str = ""
    status: str = "Considering"
    role: str = "Member"
    reliability_score: int = Field(default=1, ge=1, le=5)
    confidentiality_score: int = Field(default=1, ge=1, le=5)
    skill_capacity_score: int = Field(default=1, ge=1, le=5)
    financial_steadiness_score: int = Field(default=1, ge=1, le=5)
    relationship_capacity_score: int = Field(default=1, ge=1, le=5)
    possible_contribution: str = ""
    notes: str = ""
    invitation_status: str = "not_sent"
    user_id: int | None = None


class PurposePayload(BaseModel):
    community_served: str = ""
    recurring_problem: str = ""
    first_focus: str = ""
    member_contribution: str = ""
    day_100_goal: str = ""
    not_doing_yet: str = ""
    purpose_statement: str = ""


class CovenantPayload(BaseModel):
    covenant_text: str = DEFAULT_COVENANT
    version: str = "v1"
    status: str = "Draft"
    accepted_by_members: list = []


class StagePayload(BaseModel):
    target_stage: str


class StageOverridePayload(BaseModel):
    target_stage: str
    explanation: str = Field(min_length=3, max_length=5000)


def _get_society(db: Session, society_id: int) -> Society:
    society = db.query(Society).filter(Society.id == society_id).first()
    if not society:
        raise HTTPException(status_code=404, detail="Society not found")
    return society


def _require_member_access(db: Session, user: User, society: Society) -> None:
    if society.is_main_hub:
        return
    if society.founder_user_id == user.id:
        return
    membership = db.query(SocietyMembership).filter(SocietyMembership.society_id == society.id, SocietyMembership.user_id == user.id, SocietyMembership.status == "active").first()
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden")


def _require_manage_access(db: Session, user: User, society: Society) -> None:
    if not can_manage_society(db, user.id, society):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/main-hub")
def main_hub(current_user: User | None = Depends(get_current_user), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    hub = seed_simba_main_hub(db)
    children = db.query(Society).filter(Society.parent_society_id == hub.id, Society.affiliation_status.in_(["approved", "active"])).all()
    return {"ok": True, "main_hub": safe_society_summary(db, hub), "approved_chapters": [safe_society_summary(db, c) for c in children]}


@router.get("/my-societies")
def my_societies(current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    ids = {sid for (sid,) in db.query(SocietyMembership.society_id).filter(SocietyMembership.user_id == current_user.id, SocietyMembership.status == "active").all()}
    societies = db.query(Society).filter((Society.founder_user_id == current_user.id) | (Society.id.in_(ids or {-1}))).all()
    return {"ok": True, "societies": [safe_society_summary(db, s) for s in societies]}


@router.post("/societies")
def create_society(payload: SocietyPayload, current_user: User = Depends(require_permission("society_builder:create_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    root_id = payload.root_society_id
    if payload.parent_society_id and root_id is None:
        parent = _get_society(db, payload.parent_society_id)
        root_id = parent.root_society_id or parent.id
    society = Society(slug=unique_society_slug(db, payload.name), founder_user_id=current_user.id, lifecycle_stage="Exploring", **payload.model_dump(exclude={"root_society_id"}))
    society.root_society_id = root_id
    db.add(society)
    db.flush()
    db.add(SocietyMembership(society_id=society.id, user_id=current_user.id, role="Founder/Admin", status="active"))
    audit(db, actor_user_id=current_user.id, action="society_created", entity_id=society.id, after=safe_society_summary(db, society))
    db.commit()
    db.refresh(society)
    return {"ok": True, "society": safe_society_summary(db, society)}


@router.get("/societies/{society_id}")
def get_society(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    return {"ok": True, "society": safe_society_summary(db, society), "first_ten_summary": first_ten_summary(db, society.id)}


@router.patch("/societies/{society_id}")
def patch_society(society_id: int, payload: SocietyPatchPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(society, key, value or "" if key not in {"parent_society_id", "root_society_id"} else value)
    db.commit()
    return {"ok": True, "society": safe_society_summary(db, society)}


@router.post("/societies/{society_id}/apply-chapter")
def apply_chapter(society_id: int, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    before = {"affiliation_status": society.affiliation_status, "is_chapter": society.is_chapter}
    society.affiliation_status = "pending_review"
    society.is_chapter = True
    audit(db, actor_user_id=current_user.id, action="chapter_application_submitted", entity_id=society.id, before=before, after={"affiliation_status": society.affiliation_status, "is_chapter": society.is_chapter})
    db.commit()
    return {"ok": True, "society": safe_society_summary(db, society)}


@router.post("/societies/{society_id}/blueprint-audit")
def save_blueprint(society_id: int, payload: BlueprintPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    data = payload.model_dump()
    logic = blueprint_logic(data)
    row = SocietyBlueprintAudit(society_id=society.id, **data, **logic)
    db.add(row)
    audit(db, actor_user_id=current_user.id, action="blueprint_audit_completed", entity_id=society.id, after=logic)
    db.commit()
    db.refresh(row)
    return {"ok": True, "blueprint_audit": {**data, **logic, "id": row.id}}


@router.get("/societies/{society_id}/blueprint-audit/latest")
def latest_blueprint(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    row = db.query(SocietyBlueprintAudit).filter_by(society_id=society.id).order_by(SocietyBlueprintAudit.created_at.desc(), SocietyBlueprintAudit.id.desc()).first()
    return {"ok": True, "blueprint_audit": None if not row else {c.name: getattr(row, c.name) for c in row.__table__.columns}}


@router.post("/societies/{society_id}/first-ten")
def add_first_ten(society_id: int, payload: FirstTenPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    row = SocietyFirstTenMember(society_id=society.id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, actor_user_id=current_user.id, action="first_ten_member_added", entity_id=society.id, after={"member_id": row.id, "role": row.role, "status": row.status})
    db.commit()
    return {"ok": True, "member": {c.name: getattr(row, c.name) for c in row.__table__.columns}, "summary": first_ten_summary(db, society.id)}


@router.patch("/societies/{society_id}/first-ten/{member_id}")
def update_first_ten(society_id: int, member_id: int, payload: FirstTenPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    row = db.query(SocietyFirstTenMember).filter_by(id=member_id, society_id=society.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="First Ten member not found")
    before = {"role": row.role, "status": row.status}
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    audit(db, actor_user_id=current_user.id, action="first_ten_member_updated", entity_id=society.id, before=before, after={"member_id": row.id, "role": row.role, "status": row.status})
    db.commit()
    return {"ok": True, "summary": first_ten_summary(db, society.id)}


@router.delete("/societies/{society_id}/first-ten/{member_id}")
def delete_first_ten(society_id: int, member_id: int, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    row = db.query(SocietyFirstTenMember).filter_by(id=member_id, society_id=society.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="First Ten member not found")
    db.delete(row)
    db.commit()
    return {"ok": True, "summary": first_ten_summary(db, society.id)}


@router.post("/societies/{society_id}/purpose")
def save_purpose(society_id: int, payload: PurposePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    statement, prompt = purpose_statement_and_prompt(payload.model_dump())
    row = SocietyPurpose(society_id=society.id, **payload.model_dump(exclude={"purpose_statement"}), purpose_statement=payload.purpose_statement or statement, refinement_prompt=prompt)
    db.add(row)
    society.community_served = payload.community_served or society.community_served
    society.first_focus = payload.first_focus or society.first_focus
    audit(db, actor_user_id=current_user.id, action="purpose_saved", entity_id=society.id, after={"purpose_statement": row.purpose_statement, "refinement_prompt": prompt})
    db.commit()
    return {"ok": True, "purpose": {c.name: getattr(row, c.name) for c in row.__table__.columns}}


@router.post("/societies/{society_id}/covenant")
def save_covenant(society_id: int, payload: CovenantPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    if payload.status not in COVENANT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid covenant status")
    row = SocietyCovenant(society_id=society.id, **payload.model_dump())
    db.add(row)
    audit(db, actor_user_id=current_user.id, action="covenant_saved", entity_id=society.id, after={"status": row.status, "version": row.version})
    db.commit()
    return {"ok": True, "covenant": {c.name: getattr(row, c.name) for c in row.__table__.columns}}


@router.post("/societies/{society_id}/advance-stage")
def advance_stage(society_id: int, payload: StagePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    ok, missing = stage_eligibility(db, society, payload.target_stage)
    if not ok:
        return {"ok": False, "advanced": False, "missing": missing, "society": safe_society_summary(db, society)}
    before = {"lifecycle_stage": society.lifecycle_stage}
    society.lifecycle_stage = payload.target_stage
    audit(db, actor_user_id=current_user.id, action="lifecycle_stage_changed", entity_id=society.id, before=before, after={"lifecycle_stage": society.lifecycle_stage})
    db.commit()
    return {"ok": True, "advanced": True, "society": safe_society_summary(db, society)}


@router.get("/admin/chapter-applications")
def chapter_applications(current_user: User = Depends(require_permission("society_builder:review_chapters")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    societies = db.query(Society).filter(Society.affiliation_status == "pending_review").all()
    return {"ok": True, "applications": [safe_society_summary(db, s) for s in societies]}


def _set_chapter_status(db: Session, society_id: int, current_user: User, status_value: str, action: str):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    before = {"affiliation_status": society.affiliation_status}
    society.affiliation_status = status_value
    society.is_chapter = status_value in {"approved", "active", "pending_review", "changes_requested"}
    audit(db, actor_user_id=current_user.id, action=action, entity_id=society.id, before=before, after={"affiliation_status": status_value})
    db.commit()
    return {"ok": True, "society": safe_society_summary(db, society)}


@router.post("/admin/chapter-applications/{society_id}/approve")
def approve_chapter(society_id: int, current_user: User = Depends(require_permission("society_builder:review_chapters")), db: Session = Depends(get_db)):
    return _set_chapter_status(db, society_id, current_user, "approved", "chapter_approved")


@router.post("/admin/chapter-applications/{society_id}/request-changes")
def chapter_changes(society_id: int, current_user: User = Depends(require_permission("society_builder:review_chapters")), db: Session = Depends(get_db)):
    return _set_chapter_status(db, society_id, current_user, "changes_requested", "chapter_changes_requested")


@router.post("/admin/chapter-applications/{society_id}/decline")
def decline_chapter(society_id: int, current_user: User = Depends(require_permission("society_builder:review_chapters")), db: Session = Depends(get_db)):
    return _set_chapter_status(db, society_id, current_user, "declined", "chapter_declined")


@router.post("/admin/societies/{society_id}/stage-override")
def stage_override(society_id: int, payload: StageOverridePayload, current_user: User = Depends(require_permission("society_builder:override_stage")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    before = {"lifecycle_stage": society.lifecycle_stage}
    society.lifecycle_stage = payload.target_stage
    audit(db, actor_user_id=current_user.id, action="lifecycle_stage_overridden", entity_id=society.id, before=before, after={"lifecycle_stage": society.lifecycle_stage, "explanation": payload.explanation})
    db.commit()
    return {"ok": True, "society": safe_society_summary(db, society)}
