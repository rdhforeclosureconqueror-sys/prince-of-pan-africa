from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.authz import user_has_permission
from app.dependencies.auth import get_current_user, require_auth, require_permission
from app.models import Society, SocietyBlueprintAudit, SocietyRoleOpening, SocietyRoleCandidateReview, SocietyRoleDiscussionNote, SocietyRoleAppointmentHistory, SocietyContainer, SocietyContainerMilestone, SocietyCovenant, SocietyFirstTenMember, SocietyInstitutionalProfile, SocietyMembership, SocietyPurpose, SocietyTrustTask, User, Audiobook, AudiobookChapter
from app.services.society_intelligence import generate_society_intelligence
from app.services.institution_intelligence import generate_institution_intelligence
from app.services.opportunity_intelligence import generate_opportunity_intelligence
from app.services.society_builder import (
    DEFAULT_COVENANT,
    FIRST_CONTAINER_TYPE,
    TRUST_TASK_STATUSES,
    activate_first_container,
    audit,
    blueprint_logic,
    can_manage_society,
    container_dict,
    first_ten_summary,
    active_membership,
    profile_dict,
    purpose_statement_and_prompt,
    require_society_builder_enabled,
    safe_society_summary,
    recalculate_container_progress,
    seed_simba_main_hub,
    society_directory,
    society_profile_presets,
    stage_eligibility,
    task_dict,
    unique_society_slug,
    HANDBOOK_BOOK_SLUG,
    HANDBOOK_TITLE,
)

logger = logging.getLogger(__name__)

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


class InstitutionalProfilePayload(BaseModel):
    display_name: str = ""
    headline: str = ""
    primary_contribution: str = ""
    contribution_categories_json: list = []
    availability: str = ""
    contribution_type: str = "Volunteer"
    looking_for_json: list = []
    skills_to_learn_json: list = []
    goals_json: list = []
    needs_json: list = []
    needs_privacy_level: str = "Care Team Only"
    current_projects_json: list = []
    impact_summary_json: dict = {}
    visibility: str = "Society Members"


class TrustTaskPatchPayload(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    lane: str | None = None
    owner_member_id: int | None = None
    linked_role: str | None = None
    due_date: str | None = None
    blocked_reason: str | None = None
    completion_notes: str | None = None
    priority: str | None = None


class TrustTaskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    milestone_id: int | None = None
    status: str = "backlog"
    lane: str = "systems"
    task_type: str = "manual"
    owner_member_id: int | None = None
    linked_role: str = ""
    linked_module: str = ""
    linked_handbook_chapter: str = ""
    linked_container_step: str = ""
    due_date: str | None = None
    priority: str = "normal"
    blocked_reason: str = ""


class RoleOpeningPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    purpose: str = ""
    responsibilities: list[str] = []
    required_behaviors: list[str] = []
    handbook_chapters: list[str] = []
    recommended_assessments: list[str] = []


class ReviewerNotesPayload(BaseModel):
    reviewer_notes: str = ""


class DiscussionNotePayload(BaseModel):
    candidate_review_id: int | None = None
    note: str = Field(min_length=1, max_length=5000)


class DecisionPayload(BaseModel):
    decision: str
    reason: str = ""
    start_date: str | None = None
    review_date: str | None = None
    mentor: str = ""
    training_status: str = "Not started"




def _chapter_number(label: str) -> int | None:
    import re
    match = re.search(r"(?:chapter|week)\s+(\d+)", label or "", re.IGNORECASE)
    return int(match.group(1)) if match else None

def _resolve_task_reader_reference(db: Session, task: SocietyTrustTask, user: User) -> dict:
    label = task.source_chapter_label or task.linked_handbook_chapter or ""
    if task.source_reader_path:
        return {"connected": True, "reader_path": task.source_reader_path}
    book = None
    if task.source_book_id:
        book = db.query(Audiobook).filter(Audiobook.id == task.source_book_id).first()
    if not book:
        title_candidates = {HANDBOOK_TITLE.lower(), (task.source_book_slug or HANDBOOK_BOOK_SLUG).replace("-", " ").lower()}
        books = db.query(Audiobook).filter((Audiobook.user_id == user.id) | (Audiobook.access_level.in_(["public", "free", "subscription", "member", "subscriber"]))).all()
        book = next((b for b in books if (b.title or "").strip().lower() in title_candidates), None)
    if not book:
        return {"connected": False, "reader_path": "/study", "message": "Chapter link will open when the handbook is connected.", "book_slug": task.source_book_slug or HANDBOOK_BOOK_SLUG, "book_title": HANDBOOK_TITLE}
    chapter = None
    if task.source_section_id:
        chapter = db.query(AudiobookChapter).filter(AudiobookChapter.id == task.source_section_id, AudiobookChapter.audiobook_id == book.id).first()
    if not chapter:
        number = _chapter_number(label)
        if number:
            chapter = db.query(AudiobookChapter).filter(AudiobookChapter.audiobook_id == book.id, AudiobookChapter.chapter_index == number).first()
        if not chapter and label:
            chapter = next((c for c in book.chapters if label.lower() in (c.title or "").lower()), None)
    if not chapter:
        return {"connected": False, "reader_path": f"/study?book={book.id}", "message": "Chapter link will open when the handbook section is connected.", "book_id": book.id, "book_title": book.title}
    return {"connected": True, "reader_path": f"/study?book={book.id}&chapter={chapter.chapter_index}", "book_id": book.id, "section_id": chapter.id, "chapter_index": chapter.chapter_index, "chapter_title": chapter.title}

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


@router.get("/societies/{society_id}/institutional-profile/me")
def get_my_institutional_profile(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    profile = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id, user_id=current_user.id).first()
    return {"ok": True, "society": safe_society_summary(db, society), "profile": profile_dict(profile), "presets": society_profile_presets(society)}


def _upsert_profile(db: Session, society: Society, user: User, payload: InstitutionalProfilePayload) -> SocietyInstitutionalProfile:
    membership = active_membership(db, society.id, user.id)
    profile = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id, user_id=user.id).first()
    if profile is None:
        profile = SocietyInstitutionalProfile(society_id=society.id, user_id=user.id, society_membership_id=membership.id if membership else None)
        db.add(profile)
    data = payload.model_dump()
    if data.get("needs_privacy_level") not in {"Care Team Only", "Admin Only", "Private", "Society Members"}:
        data["needs_privacy_level"] = "Care Team Only"
    for key, value in data.items():
        setattr(profile, key, value)
    if not profile.display_name:
        profile.display_name = user.email.split("@", 1)[0]
    return profile


@router.post("/societies/{society_id}/institutional-profile/me")
def create_my_institutional_profile(society_id: int, payload: InstitutionalProfilePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    profile = _upsert_profile(db, society, current_user, payload)
    db.commit()
    db.refresh(profile)
    return {"ok": True, "profile": profile_dict(profile), "presets": society_profile_presets(society)}


@router.patch("/societies/{society_id}/institutional-profile/me")
def patch_my_institutional_profile(society_id: int, payload: InstitutionalProfilePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    return create_my_institutional_profile(society_id, payload, current_user, db)


@router.get("/societies/{society_id}/member-home")
def society_member_home(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    profile = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id, user_id=current_user.id).first()
    directory = society_directory(db, society.id)
    newest = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id).order_by(SocietyInstitutionalProfile.created_at.desc()).limit(5).all()
    active_container = db.query(SocietyContainer).filter_by(society_id=society.id, status="active").order_by(SocietyContainer.created_at.desc(), SocietyContainer.id.desc()).first()
    active_container_summary = container_dict(db, active_container) if active_container else None
    return {
        "ok": True,
        "society": safe_society_summary(db, society),
        "active_container": active_container_summary,
        "profile": profile_dict(profile),
        "presets": society_profile_presets(society),
        "directory_highlights": directory["groups"][:4],
        "newest_members": [profile_dict(p, include_private=False) for p in newest],
        "contribution_flow": "Future versions will show how your membership contribution supports Simba, your chosen society, and approved projects.",
    }


@router.get("/societies/{society_id}/directory")
def get_society_directory(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    return {"ok": True, "society": safe_society_summary(db, society), "directory": society_directory(db, society.id), "presets": society_profile_presets(society)}




@router.get("/societies/{society_id}/intelligence")
def society_intelligence(society_id: int, debug: bool = False, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    include_debug = debug and user_has_permission(db, current_user, "society_builder:read_admin")
    try:
        return generate_society_intelligence(db, society_id=society.id, include_debug=include_debug)
    except ValueError:
        raise HTTPException(status_code=404, detail="Society not found")


@router.get("/institutions/{institution_id}/intelligence")
def institution_intelligence(institution_id: int, debug: bool = False, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    institution = _get_society(db, institution_id)
    _require_member_access(db, current_user, institution)
    include_debug = debug and user_has_permission(db, current_user, "society_builder:read_admin")
    try:
        return generate_institution_intelligence(db, institution_id=institution.id, include_debug=include_debug)
    except ValueError:
        raise HTTPException(status_code=404, detail="Institution not found")


@router.get("/opportunities/intelligence")
def opportunity_intelligence(society_id: int | None = None, debug: bool = False, current_user: User = Depends(require_permission("society_builder:read_admin")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    include_debug = debug and user_has_permission(db, current_user, "society_builder:read_admin")
    try:
        return generate_opportunity_intelligence(db, society_id=society_id, include_debug=include_debug)
    except ValueError:
        raise HTTPException(status_code=404, detail="Society not found")

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



@router.post("/societies/{society_id}/containers/first-100-days/activate")
def activate_first_100_days_container(society_id: int, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    try:
        container = activate_first_container(db, society, current_user.id)
        db.commit()
        db.refresh(container)
        return {"ok": True, "container": container_dict(db, container)}
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("first_100_days_activation_database_error society_id=%s actor_user_id=%s", society.id, current_user.id)
        raise HTTPException(status_code=500, detail={"code": "first_container_activation_database_error", "message": "First 100 Days Container activation failed while writing to the database. Check production logs for the exact migration, column, constraint, or insert error.", "society_id": society.id}) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("first_100_days_activation_unexpected_error society_id=%s actor_user_id=%s", society.id, current_user.id)
        raise HTTPException(status_code=500, detail={"code": "first_container_activation_failed", "message": "First 100 Days Container activation failed unexpectedly. Check production logs for the exact exception.", "society_id": society.id}) from exc


@router.get("/societies/{society_id}/containers/active")
def active_container(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    container = db.query(SocietyContainer).filter_by(society_id=society.id, status="active").order_by(SocietyContainer.created_at.desc(), SocietyContainer.id.desc()).first()
    return {"ok": True, "container": container_dict(db, container) if container else None, "start_available": container is None}


@router.get("/societies/{society_id}/trust-board")
def trust_board(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    container = db.query(SocietyContainer).filter_by(society_id=society.id, status="active").order_by(SocietyContainer.created_at.desc(), SocietyContainer.id.desc()).first()
    if not container:
        return {"ok": True, "container": None, "columns": {status: [] for status in ["backlog", "this_week", "in_progress", "waiting", "completed"]}}
    recalculate_container_progress(db, container)
    db.commit()
    tasks = db.query(SocietyTrustTask).filter_by(container_id=container.id).order_by(SocietyTrustTask.id.asc()).all()
    columns = {status: [] for status in ["backlog", "this_week", "in_progress", "waiting", "completed"]}
    for task in tasks:
        if task.status in columns:
            columns[task.status].append(task_dict(task))
    return {"ok": True, "container": container_dict(db, container), "columns": columns}



@router.get("/societies/{society_id}/trust-board/tasks/{task_id}/reader-reference")
def trust_task_reader_reference(society_id: int, task_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    task = db.query(SocietyTrustTask).filter_by(id=task_id, society_id=society.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True, "reference": _resolve_task_reader_reference(db, task, current_user)}

@router.post("/societies/{society_id}/trust-board/tasks")
def create_trust_task(society_id: int, payload: TrustTaskCreatePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    if payload.status not in TRUST_TASK_STATUSES or payload.lane not in {"people", "systems", "projects", "community_impact"}:
        raise HTTPException(status_code=400, detail="Invalid task status or lane")
    container = db.query(SocietyContainer).filter_by(society_id=society.id, status="active").first()
    if not container:
        raise HTTPException(status_code=404, detail="No active container")
    data = payload.model_dump()
    row = SocietyTrustTask(society_id=society.id, container_id=container.id, created_by=current_user.id, created_from_template=False, **data)
    if row.status == "completed":
        row.completed_at = datetime.utcnow()
    db.add(row)
    audit(db, actor_user_id=current_user.id, action="trust_task_created", entity_id=society.id, after={"task": row.title})
    recalculate_container_progress(db, container)
    db.commit()
    db.refresh(row)
    return {"ok": True, "task": task_dict(row), "container": container_dict(db, container)}


@router.patch("/societies/{society_id}/trust-board/tasks/{task_id}")
def update_trust_task(society_id: int, task_id: int, payload: TrustTaskPatchPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    task = db.query(SocietyTrustTask).filter_by(id=task_id, society_id=society.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    membership = active_membership(db, society.id, current_user.id)
    can_manage = can_manage_society(db, current_user.id, society)
    if not can_manage and (not membership or task.owner_member_id != membership.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") and data["status"] not in TRUST_TASK_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid task status")
    if data.get("lane") and data["lane"] not in {"people", "systems", "projects", "community_impact"}:
        raise HTTPException(status_code=400, detail="Invalid task lane")
    if not can_manage:
        data = {k: v for k, v in data.items() if k in {"status", "blocked_reason", "completion_notes"}}
    before = {"status": task.status}
    for key, value in data.items():
        setattr(task, key, value or "" if key in {"blocked_reason", "completion_notes", "description"} else value)
    if task.status == "completed" and task.completed_at is None:
        task.completed_at = datetime.utcnow()
    if task.status != "completed":
        task.completed_at = None
    container = db.query(SocietyContainer).filter_by(id=task.container_id).first()
    audit(db, actor_user_id=current_user.id, action="trust_task_updated", entity_id=society.id, before=before, after={"task_id": task.id, "status": task.status})
    if container:
        recalculate_container_progress(db, container)
    db.commit()
    db.refresh(task)
    return {"ok": True, "task": task_dict(task), "container": container_dict(db, container) if container else None}

def _row_public(row) -> dict | None:
    return None if row is None else {c.name: getattr(row, c.name) for c in row.__table__.columns}


def _parse_date(value: str | None, fallback: date | None = None) -> date | None:
    if not value:
        return fallback
    return date.fromisoformat(value)


def _role_opening_or_404(db: Session, society_id: int, role_id: int) -> SocietyRoleOpening:
    row = db.query(SocietyRoleOpening).filter_by(id=role_id, society_id=society_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Role opening not found")
    return row


def _review_or_404(db: Session, society_id: int, role_id: int, review_id: int) -> SocietyRoleCandidateReview:
    row = db.query(SocietyRoleCandidateReview).filter_by(id=review_id, society_id=society_id, role_opening_id=role_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate review not found")
    return row


def _candidate_name(member: SocietyFirstTenMember | None) -> str:
    return member.name if member else "Unknown member"


def _candidate_fit(role: SocietyRoleOpening, member: SocietyFirstTenMember, teammates: list[SocietyFirstTenMember]) -> dict:
    behaviors = [b.lower() for b in (role.required_behaviors or [])]
    evidence = []
    strengths = []
    growth = []
    score = 0
    if member.reliability_score >= 4:
        evidence.append("Behavioral evidence: dependable follow-through in the First Ten profile."); strengths.append("Reliability"); score += 2
    if member.confidentiality_score >= 4:
        evidence.append("Behavioral evidence: trusted with sensitive information in confidentiality observations."); strengths.append("Confidentiality"); score += 2
    if member.relationship_capacity_score >= 4:
        evidence.append("Behavioral evidence: steady relationship capacity and collaboration."); strengths.append("Relationship capacity"); score += 2
    if member.skill_capacity_score >= 4:
        evidence.append("Behavioral evidence: practical skill capacity for shared responsibilities."); strengths.append("Skill capacity"); score += 2
    if member.financial_steadiness_score >= 4:
        evidence.append("Behavioral evidence: financial steadiness for roles involving resources or records."); strengths.append("Financial steadiness"); score += 2
    if any(word in " ".join(behaviors) for word in ["finance", "money", "treasury", "transparent"]):
        if member.financial_steadiness_score >= 4: score += 1
        else: growth.append("Practice two-person financial review before carrying treasury responsibility.")
    if any(word in " ".join(behaviors) for word in ["listen", "facilitat", "meeting"]):
        if member.relationship_capacity_score >= 4: score += 1
        else: growth.append("Shadow meeting facilitation and receive mentoring on listening practices.")
    if member.notes:
        evidence.append(member.notes)
    if member.possible_contribution:
        strengths.append(member.possible_contribution)
    if not growth:
        growth.append("Continue role-specific practice with a mentor and document learning after the first review cycle.")
    if score >= 8:
        label = "Strong Alignment"
    elif score >= 5:
        label = "Good Alignment"
    else:
        label = "Emerging Alignment"
    confidence = "Substantial community evidence" if score >= 8 else "Developing community evidence" if score >= 5 else "Limited evidence; review with care"
    completed = {"First Ten behavioral profile"}
    missing = [a for a in (role.recommended_assessments or []) if a not in completed]
    complements = [m.name for m in teammates if m.id != member.id and (m.reliability_score >= 4 or m.relationship_capacity_score >= 4)][:3]
    return {"alignment_label": label, "behavioral_confidence": confidence, "behavioral_evidence": evidence or ["No behavioral notes recorded yet."], "assessment_evidence": list(completed), "growth_path": growth, "missing_assessments": missing, "current_strengths": strengths or ["Invite reviewers to record observed strengths."], "handbook_references": role.handbook_chapters or [], "complementary_teammates": complements}


def _development_plan(role: SocietyRoleOpening, review: SocietyRoleCandidateReview) -> dict:
    return {"suggested_assessments": review.missing_assessments or role.recommended_assessments or ["Role fit reflection"], "handbook_chapters": role.handbook_chapters or ["Mutual Aid Society operating handbook"], "recommended_mentor": (review.complementary_teammates or ["Society facilitator"])[0], "suggested_practice_opportunities": ["Shadow the role in one meeting", "Co-lead a small responsibility", "Review notes with a mentor"], "estimated_review_timeline": "Review again in 30–60 days"}

@router.get("/societies/{society_id}/role-assignment/dashboard")
def role_assignment_dashboard(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_member_access(db, current_user, society)
    openings = db.query(SocietyRoleOpening).filter_by(society_id=society.id).order_by(SocietyRoleOpening.created_at.desc()).all()
    reviews = db.query(SocietyRoleCandidateReview).filter_by(society_id=society.id).all()
    history = db.query(SocietyRoleAppointmentHistory).filter_by(society_id=society.id).order_by(SocietyRoleAppointmentHistory.created_at.desc()).all()
    return {"ok": True, "society": safe_society_summary(db, society), "current_members": first_ten_summary(db, society.id), "open_roles": [_row_public(r) for r in openings if r.status == "open"], "filled_roles": [_row_public(r) for r in openings if r.status == "appointed"], "vacant_roles": [_row_public(r) for r in openings if r.status in {"open", "under_review"}], "roles_under_review": [_row_public(r) for r in openings if r.status == "under_review"], "recently_appointed": [_row_public(h) for h in history[:5]], "needs_development": [_row_public(r) for r in reviews if r.decision == "needs_development"], "upcoming_reviews": [_row_public(h) for h in history if h.review_date][:10]}


@router.post("/societies/{society_id}/role-assignment/open-roles")
def create_role_opening(society_id: int, payload: RoleOpeningPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    _require_manage_access(db, current_user, society)
    row = SocietyRoleOpening(society_id=society.id, created_by=current_user.id, **payload.model_dump())
    db.add(row); db.flush()
    audit(db, actor_user_id=current_user.id, action="role_opened", entity_id=society.id, after={"role_opening_id": row.id, "title": row.title})
    db.commit(); db.refresh(row)
    return {"ok": True, "role": _row_public(row)}


@router.get("/societies/{society_id}/role-assignment/open-roles/{role_id}")
def get_role_opening(society_id: int, role_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_member_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id)
    reviews = db.query(SocietyRoleCandidateReview).filter_by(role_opening_id=role.id).all()
    return {"ok": True, "society": safe_society_summary(db, society), "role": _row_public(role), "candidate_reviews": [_row_public(r) for r in reviews]}


@router.post("/societies/{society_id}/role-assignment/open-roles/{role_id}/suggest-candidates")
def suggest_role_candidates(society_id: int, role_id: int, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_manage_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id)
    members = db.query(SocietyFirstTenMember).filter_by(society_id=society.id).order_by(SocietyFirstTenMember.created_at.asc(), SocietyFirstTenMember.id.asc()).all()
    groups = {"Strong Alignment": [], "Good Alignment": [], "Emerging Alignment": []}
    for member in members:
        fit = _candidate_fit(role, member, members)
        review = db.query(SocietyRoleCandidateReview).filter_by(role_opening_id=role.id, candidate_member_id=member.id).first()
        if not review:
            review = SocietyRoleCandidateReview(society_id=society.id, role_opening_id=role.id, candidate_member_id=member.id, created_by=current_user.id)
            db.add(review)
        for k, v in fit.items(): setattr(review, k, v)
        db.flush()
        groups[fit["alignment_label"]].append({"candidate_member": _row_public(member), "review": _row_public(review)})
    role.status = "under_review"
    audit(db, actor_user_id=current_user.id, action="role_candidates_suggested", entity_id=society.id, after={"role_opening_id": role.id})
    db.commit()
    return {"ok": True, "role": _row_public(role), "suggested_candidates": groups, "language_guardrail": "No ranking numbers, percentages, Best label, AI appointments, or automatic promotions are used."}


@router.get("/societies/{society_id}/role-assignment/open-roles/{role_id}/reviews/{review_id}")
def get_candidate_review(society_id: int, role_id: int, review_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_member_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id); review = _review_or_404(db, society.id, role.id, review_id)
    candidate = db.query(SocietyFirstTenMember).filter_by(id=review.candidate_member_id).first()
    notes = db.query(SocietyRoleDiscussionNote).filter_by(candidate_review_id=review.id).order_by(SocietyRoleDiscussionNote.created_at.asc()).all()
    return {"ok": True, "candidate": _row_public(candidate), "role": _row_public(role), "review": _row_public(review), "discussion_notes": [_row_public(n) for n in notes]}


@router.patch("/societies/{society_id}/role-assignment/open-roles/{role_id}/reviews/{review_id}")
def update_candidate_review_notes(society_id: int, role_id: int, review_id: int, payload: ReviewerNotesPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_manage_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id); review = _review_or_404(db, society.id, role.id, review_id)
    review.reviewer_notes = payload.reviewer_notes
    audit(db, actor_user_id=current_user.id, action="role_candidate_review_note_updated", entity_id=society.id, after={"review_id": review.id})
    db.commit(); db.refresh(review)
    return {"ok": True, "review": _row_public(review)}


@router.post("/societies/{society_id}/role-assignment/open-roles/{role_id}/discussion-notes")
def add_discussion_note(society_id: int, role_id: int, payload: DiscussionNotePayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_manage_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id)
    row = SocietyRoleDiscussionNote(society_id=society.id, role_opening_id=role.id, candidate_review_id=payload.candidate_review_id, note=payload.note, created_by=current_user.id)
    db.add(row); db.flush(); audit(db, actor_user_id=current_user.id, action="role_discussion_note_added", entity_id=society.id, after={"note_id": row.id})
    db.commit(); db.refresh(row)
    return {"ok": True, "discussion_note": _row_public(row)}


@router.post("/societies/{society_id}/role-assignment/open-roles/{role_id}/reviews/{review_id}/decision")
def record_role_decision(society_id: int, role_id: int, review_id: int, payload: DecisionPayload, current_user: User = Depends(require_permission("society_builder:update_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_manage_access(db, current_user, society)
    role = _role_opening_or_404(db, society.id, role_id); review = _review_or_404(db, society.id, role.id, review_id)
    allowed = {"appoint", "delay", "needs_development", "not_needed_right_now"}
    if payload.decision not in allowed: raise HTTPException(status_code=400, detail="Decision must be Appoint, Delay, Needs Development, or Not Needed Right Now")
    review.decision = payload.decision
    appointment = None
    if payload.decision == "appoint":
        notes = db.query(SocietyRoleDiscussionNote).filter_by(role_opening_id=role.id).all()
        appointment = SocietyRoleAppointmentHistory(society_id=society.id, role_opening_id=role.id, candidate_member_id=review.candidate_member_id, role_title=role.title, start_date=_parse_date(payload.start_date, date.today()), reason=payload.reason, supporting_evidence=review.behavioral_evidence + review.assessment_evidence, community_notes=[n.note for n in notes], review_date=_parse_date(payload.review_date, date.today() + timedelta(days=90)), mentor=payload.mentor, training_status=payload.training_status, created_by=current_user.id)
        db.add(appointment); role.status = "appointed"
    else:
        review.development_plan = _development_plan(role, review); role.status = "open" if payload.decision == "not_needed_right_now" else "under_review"
    audit(db, actor_user_id=current_user.id, action="role_appointment_decision_recorded", entity_id=society.id, after={"review_id": review.id, "decision": payload.decision})
    db.commit()
    return {"ok": True, "software_boundary": "The software recorded the community decision; it did not appoint anyone automatically.", "review": _row_public(review), "appointment": _row_public(appointment)}


@router.get("/societies/{society_id}/role-assignment/appointment-history")
def appointment_history(society_id: int, current_user: User = Depends(require_permission("society_builder:read_self")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id); _require_member_access(db, current_user, society)
    rows = db.query(SocietyRoleAppointmentHistory).filter_by(society_id=society.id).order_by(SocietyRoleAppointmentHistory.created_at.desc()).all()
    return {"ok": True, "history": [_row_public(r) for r in rows]}

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

@router.get("/admin/societies/{society_id}/institutional-profiles")
def admin_institutional_profiles(society_id: int, current_user: User = Depends(require_permission("admin:read_dashboard")), db: Session = Depends(get_db)):
    require_society_builder_enabled(db, current_user)
    society = _get_society(db, society_id)
    profiles = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id).order_by(SocietyInstitutionalProfile.updated_at.desc()).all()
    return {"ok": True, "society": safe_society_summary(db, society), "profiles": [profile_dict(p) for p in profiles]}
