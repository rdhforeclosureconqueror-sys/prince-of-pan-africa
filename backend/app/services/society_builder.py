from __future__ import annotations

import os
import re
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.models import (
    MutualAidAuditLog,
    Society,
    SocietyBlueprintAudit,
    SocietyCovenant,
    SocietyFirstTenMember,
    SocietyInstitutionalProfile,
    SocietyMembership,
    SocietyPurpose,
)

SIMBA_MAIN_HUB_SLUG = "simba-main-hub"
SIMBA_MAIN_HUB_NAME = "Simba Mutual Aid Society"
CRITICAL_FIRST_TEN_ROLES = {"Facilitator", "Treasurer", "Assistant Treasurer", "Recordkeeper", "Care Coordinator"}
BLUEPRINT_ORDER = [
    ("trust_score", "Trust", "Blueprint Audit"),
    ("relationships_score", "Relationships", "Name Your First Ten"),
    ("mutual_aid_score", "Mutual Aid", "Purpose Builder"),
    ("organization_score", "Organization", "Covenant"),
    ("institutions_score", "Institutions", "Foundation Phase"),
    ("businesses_score", "Businesses", "Build trust before business support"),
    ("property_score", "Property", "Build records before property work"),
    ("community_wealth_score", "Community Wealth", "Strengthen the first container"),
    ("political_power_score", "Political Power", "Build institutions before political power"),
]
DEFAULT_COVENANT = """We will show up consistently.
We will contribute as agreed.
We will keep records.
We will protect privacy.
We will handle money transparently.
We will disagree without destroying the room.
We will not use the society for personal gain without disclosure.
We will honor elders and train youth.
We will build systems that can outlive us."""

SOCIETY_TYPE_PRESETS = {
    "health": ["Personal Training", "Yoga", "Massage Therapy", "Nutrition Coaching", "Walking Group", "Gardening", "Cooking", "Mental Wellness", "CPR Instruction", "Youth Coaching"],
    "business": ["Accounting", "Marketing", "Sales", "Vendor Referrals", "Grant Writing", "Business Coaching", "Technology", "Legal Referral", "Event Planning", "Photography"],
    "preparedness": ["CPR", "Transportation", "Emergency Supplies", "Communication Tree", "Elder Check-ins", "Food Storage", "Water Readiness", "Medical Support", "Evacuation Help"],
    "youth": ["Mentorship", "Tutoring", "Coaching", "Leadership Training", "Technology", "Sports", "History/Archive Projects", "Business Apprenticeship"],
}


def society_builder_enabled() -> bool:
    return os.getenv("SOCIETY_BUILDER_ENABLED", os.getenv("ENABLE_SOCIETY_BUILDER", "false")).strip().lower() in {"1", "true", "yes", "on"}


def require_society_builder_enabled(db: Session | None = None, user=None) -> None:
    if society_builder_enabled():
        return
    if db is not None and user is not None and user_has_permission(db, user, "admin:read_dashboard"):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society Builder is not enabled")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or "society"


def unique_society_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug = base
    counter = 2
    while db.query(Society).filter(Society.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def seed_simba_main_hub(db: Session) -> Society:
    hub = db.query(Society).filter(Society.slug == SIMBA_MAIN_HUB_SLUG).one_or_none()
    if hub is None:
        hub = db.query(Society).filter(Society.is_main_hub.is_(True)).one_or_none()
    if hub is None:
        hub = Society(
            slug=SIMBA_MAIN_HUB_SLUG,
            name=SIMBA_MAIN_HUB_NAME,
            type="Existing organization",
            description="The main mutual aid society, model institution, parent network, and shared infrastructure for Simba chapters.",
            community_served="Simba members and affiliated societies",
            location="National",
            first_focus="Community wealth",
            visibility="Public profile, private operations",
            lifecycle_stage="Institution Building",
            founder_user_id=None,
            parent_society_id=None,
            root_society_id=None,
            is_main_hub=True,
            is_chapter=False,
            chapter_level="main_hub",
            affiliation_status="active",
            geographic_scope="national",
        )
        db.add(hub)
        db.commit()
        db.refresh(hub)
        return hub

    changed = False
    defaults = {
        "slug": SIMBA_MAIN_HUB_SLUG,
        "name": SIMBA_MAIN_HUB_NAME,
        "type": "Existing organization",
        "chapter_level": "main_hub",
        "is_main_hub": True,
        "is_chapter": False,
        "parent_society_id": None,
        "root_society_id": None,
        "visibility": "Public profile, private operations",
        "lifecycle_stage": "Institution Building",
        "first_focus": "Community wealth",
        "geographic_scope": "national",
        "affiliation_status": "active",
    }
    for key, value in defaults.items():
        if getattr(hub, key) != value:
            setattr(hub, key, value)
            changed = True
    if changed:
        db.commit()
        db.refresh(hub)
    return hub


def audit(db: Session, *, actor_user_id: int | None, action: str, entity_id: int | None, before: dict | None = None, after: dict | None = None) -> MutualAidAuditLog:
    row = MutualAidAuditLog(
        actor_user_id=actor_user_id,
        entity_type="society",
        entity_id=entity_id,
        action=action,
        before=before or {},
        after=after or {},
    )
    db.add(row)
    return row


def can_manage_society(db: Session, user_id: int, society: Society) -> bool:
    if society.is_main_hub:
        return False
    if society.founder_user_id == user_id:
        return True
    return db.query(SocietyMembership).filter(
        SocietyMembership.society_id == society.id,
        SocietyMembership.user_id == user_id,
        SocietyMembership.status == "active",
        SocietyMembership.role.in_(["Founder/Admin", "Facilitator"]),
    ).first() is not None


def first_ten_summary(db: Session, society_id: int) -> dict:
    members = db.query(SocietyFirstTenMember).filter(SocietyFirstTenMember.society_id == society_id).all()
    roles = {m.role for m in members}
    missing = sorted(CRITICAL_FIRST_TEN_ROLES - roles)

    def avg(attr: str) -> float:
        if not members:
            return 0
        return round(sum(getattr(m, attr) for m in members) / len(members), 2)

    return {
        "total": len(members),
        "core_members": sum(1 for m in members if m.status == "Core member"),
        "invited_members": sum(1 for m in members if m.status == "Invited"),
        "accepted_members": sum(1 for m in members if m.status in {"Accepted", "Core member"}),
        "missing_critical_roles": missing,
        "critical_role_completion": len(CRITICAL_FIRST_TEN_ROLES) - len(missing),
        "average_reliability_score": avg("reliability_score"),
        "average_confidentiality_score": avg("confidentiality_score"),
        "average_skill_capacity_score": avg("skill_capacity_score"),
        "average_relationship_capacity_score": avg("relationship_capacity_score"),
        "warning": "You have not identified a Treasurer or Recordkeeper. Shared money requires clear roles before aid requests open." if {"Treasurer", "Recordkeeper"} & set(missing) else "",
    }


def blueprint_logic(scores: dict[str, int]) -> dict[str, str]:
    ordered = [(key, label, step, int(scores.get(key, 1))) for key, label, step in BLUEPRINT_ORDER]
    weakest = min(ordered, key=lambda item: item[3])
    strongest = max(ordered, key=lambda item: item[3])
    warning = ""
    foundation = min(int(scores.get("trust_score", 1)), int(scores.get("relationships_score", 1)), int(scores.get("organization_score", 1)))
    if foundation < 4 and (int(scores.get("businesses_score", 1)) >= 4 or int(scores.get("property_score", 1)) >= 4 or int(scores.get("political_power_score", 1)) >= 4):
        warning = "Businesses are not the root. They are the fruit. Build trust before complexity."
    return {"weakest_area": weakest[1], "strongest_area": strongest[1], "recommended_next_step": weakest[2], "warning": warning}


def purpose_statement_and_prompt(payload: dict) -> tuple[str, str]:
    community = (payload.get("community_served") or "the community we serve").strip()
    problem = (payload.get("recurring_problem") or payload.get("first_focus") or "our first shared problem").strip()
    contribution = (payload.get("member_contribution") or "show up consistently and contribute as agreed").strip()
    goal = (payload.get("day_100_goal") or "long-term community capacity").strip()
    text = f"We are forming a mutual aid society that {contribution} to {problem} for {community}, while building {goal}."
    vague = "help the community" in " ".join(str(payload.get(k, "")).lower() for k in ["community_served", "recurring_problem", "first_focus", "purpose_statement"])
    prompt = "Refine this purpose: name who is served, the recurring problem, the first focus, and what should exist by Day 100." if vague else ""
    return text, prompt


def _row_dict(row) -> dict | None:
    if row is None:
        return None
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def society_profile_presets(society: Society) -> dict:
    text = f"{society.type} {society.first_focus} {society.name}".lower()
    categories: list[str] = []
    for key, values in SOCIETY_TYPE_PRESETS.items():
        if key in text or (key == "health" and "wellness" in text) or (key == "business" and "support" in text):
            categories.extend(values)
    if not categories:
        categories = ["Facilitation", "Volunteering", "Care Coordination", "Event Organizing", "Teaching", "Transportation", "Resource Support"]
    return {"contribution_categories": list(dict.fromkeys([*categories, "Custom"]))}


def active_membership(db: Session, society_id: int, user_id: int) -> SocietyMembership | None:
    return db.query(SocietyMembership).filter(
        SocietyMembership.society_id == society_id,
        SocietyMembership.user_id == user_id,
        SocietyMembership.status == "active",
    ).order_by(SocietyMembership.id.asc()).first()


def profile_dict(profile: SocietyInstitutionalProfile | None, *, include_private: bool = True) -> dict | None:
    data = _row_dict(profile)
    if data and not include_private:
        data.pop("needs_json", None)
        data.pop("needs_privacy_level", None)
    return data


def society_directory(db: Session, society_id: int) -> dict:
    profiles = db.query(SocietyInstitutionalProfile).filter(
        SocietyInstitutionalProfile.society_id == society_id,
        SocietyInstitutionalProfile.visibility != "Private",
    ).order_by(SocietyInstitutionalProfile.updated_at.desc(), SocietyInstitutionalProfile.id.desc()).all()
    groups: dict[str, list[dict]] = {}
    for profile in profiles:
        categories = profile.contribution_categories_json or [profile.primary_contribution or "Custom"]
        for category in categories or ["Custom"]:
            label = str(category or "Custom").strip() or "Custom"
            groups.setdefault(label, []).append({
                "id": profile.id,
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "headline": profile.headline,
                "primary_contribution": profile.primary_contribution,
                "availability": profile.availability,
                "contribution_type": profile.contribution_type,
                "current_projects_json": profile.current_projects_json,
                "impact_summary_json": profile.impact_summary_json,
                "visibility": profile.visibility,
            })
    return {"groups": [{"category": k, "members": v} for k, v in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0].lower()))]}


def safe_society_summary(db: Session, society: Society) -> dict:
    latest_audit = db.query(SocietyBlueprintAudit).filter(SocietyBlueprintAudit.society_id == society.id).order_by(SocietyBlueprintAudit.created_at.desc(), SocietyBlueprintAudit.id.desc()).first()
    latest_purpose = db.query(SocietyPurpose).filter(SocietyPurpose.society_id == society.id).order_by(SocietyPurpose.created_at.desc(), SocietyPurpose.id.desc()).first()
    latest_covenant = db.query(SocietyCovenant).filter(SocietyCovenant.society_id == society.id).order_by(SocietyCovenant.created_at.desc(), SocietyCovenant.id.desc()).first()
    members = db.query(SocietyFirstTenMember).filter(SocietyFirstTenMember.society_id == society.id).order_by(SocietyFirstTenMember.created_at.asc(), SocietyFirstTenMember.id.asc()).all()
    first_ten = first_ten_summary(db, society.id)
    return {
        "id": society.id,
        "name": society.name,
        "type": society.type,
        "chapter_level": society.chapter_level,
        "affiliation_status": society.affiliation_status,
        "lifecycle_stage": society.lifecycle_stage,
        "parent_society_id": society.parent_society_id,
        "root_society_id": society.root_society_id,
        "is_main_hub": society.is_main_hub,
        "is_chapter": society.is_chapter,
        "member_counts": {"first_ten_total": first_ten["total"], "core_members": first_ten["core_members"], "accepted_members": first_ten["accepted_members"]},
        "critical_role_completion": first_ten["critical_role_completion"],
        "missing_critical_roles": first_ten["missing_critical_roles"],
        "blueprint_audit_completed": latest_audit is not None,
        "purpose_completed": latest_purpose is not None,
        "covenant_completed": latest_covenant is not None,
        "latest_blueprint_audit": _row_dict(latest_audit),
        "latest_purpose": _row_dict(latest_purpose),
        "latest_covenant": _row_dict(latest_covenant),
        "first_ten_members": [_row_dict(m) for m in members],
    }


def stage_eligibility(db: Session, society: Society, target_stage: str) -> tuple[bool, list[str]]:
    missing: list[str] = []
    if society.lifecycle_stage == "Exploring" and target_stage == "Forming":
        if not society.first_focus:
            missing.append("First focus selected")
        visited = db.query(SocietyBlueprintAudit).filter_by(society_id=society.id).first() or db.query(SocietyPurpose).filter_by(society_id=society.id).first()
        if not visited:
            missing.append("Visit Blueprint Audit or Purpose Builder")
        return not missing, missing
    if society.lifecycle_stage == "Forming" and target_stage == "Foundation Phase":
        if not db.query(SocietyBlueprintAudit).filter_by(society_id=society.id).first():
            missing.append("Blueprint Audit completed")
        if not db.query(SocietyPurpose).filter_by(society_id=society.id).first():
            missing.append("Purpose saved")
        first_ten = first_ten_summary(db, society.id)
        if first_ten["total"] < 3:
            missing.append("At least 3 founding members added")
        if first_ten["critical_role_completion"] < 1:
            missing.append("At least 1 critical role assigned")
        return not missing, missing
    return False, ["Later stage advancement is not part of MVP 1 yet."]
