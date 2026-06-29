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

FIRST_CONTAINER_TYPE = "first_container_100_day"
FIRST_CONTAINER_TITLE = "First Container / 100-Day Formation Container"
TRUST_TASK_STATUSES = {"backlog", "this_week", "in_progress", "waiting", "completed", "archived"}
TRUST_TASK_LANES = {"people", "systems", "projects", "community_impact"}

FIRST_CONTAINER_MILESTONE_TEMPLATES = [
    ("Understand the Blueprint", "Part One: Understand the Blueprint — chapters 1–3. Build the first trustworthy container by naming the recurring problem, completing the Blueprint Audit, and choosing the first focus.", "Part One", 15),
    ("Form the Society", "Part Two: Form the Society — chapters 4–7. Start a society, name the First Ten, save purpose, and create the covenant.", "Part Two", 20),
    ("Build the Foundation", "Part Three: Build the Operating Structure — chapters 8–13. Set treasury, ledger categories, needs map, care teams, rules, and meeting rhythm.", "Part Three", 25),
    ("Organize Operations", "Part Four: Complete the First 100 Days — chapters 14–15. Launch the 100-Day Planner and convert the handbook into weekly outputs.", "Part Four", 15),
    ("Complete First Action", "Appendix L and Week 10–12. Choose, prepare, execute, and document one small, real, measurable action.", "First Action", 15),
    ("Generate Day 100 Report", "Part Six — chapters 21–23. Generate the Day 100 Report, record recommitments, and save a next-phase plan.", "Part Six", 10),
]

FIRST_CONTAINER_TASK_TEMPLATES = {
    "Understand the Blueprint": [
        ("Complete Blueprint Audit", "Complete the Blueprint Audit inside Society Builder.", "systems", "Blueprint Audit", "Chapter 2", "blueprint_audit"),
        ("Review the sequence: Trust → Relationships → Mutual Aid → Organization → Institutions", "Discuss why the society cannot start with businesses, money, or scale.", "people", "Blueprint Audit", "Chapter 2", "sequence_review"),
        ("Identify weakest foundation area", "Use the audit to name the weakest foundation area.", "systems", "Blueprint Audit", "Chapter 2", "weakest_area"),
        ("Choose first focus", "Select the next foundation the society must strengthen.", "projects", "Purpose Builder", "Chapter 2", "first_focus"),
    ],
    "Form the Society": [
        ("Create Society", "Use Start a Society to name the society, community served, first focus, visibility, and 100-day boundary.", "systems", "Start a Society", "Chapter 4", "create_society"),
        ("Name Your First Ten", "Enter ten potential founding members with reliability, confidentiality, capacity, and possible roles.", "people", "Name Your First Ten", "Chapter 5", "first_ten"),
        ("Add at least 3 founding members", "Confirm at least three founding members are entered.", "people", "Name Your First Ten", "Chapter 5", "three_founders"),
        ("Fill at least 1 critical role", "Assign at least one critical role before moving deeper into the container.", "people", "Name Your First Ten", "Chapter 5", "critical_role"),
        ("Assign Facilitator", "Name who keeps meetings focused.", "people", "Roles", "Appendix N", "role_facilitator"),
        ("Assign Recordkeeper", "Name who protects institutional memory.", "people", "Roles", "Appendix N", "role_recordkeeper"),
        ("Assign Treasurer", "Name who coordinates treasury records.", "people", "Roles", "Appendix N", "role_treasurer"),
        ("Assign Assistant Treasurer", "Name who provides two-person oversight.", "people", "Roles", "Appendix N", "role_assistant_treasurer"),
        ("Assign Care Coordinator", "Name who organizes care teams.", "people", "Roles", "Appendix N", "role_care_coordinator"),
    ],
    "Build the Foundation": [
        ("Save Purpose Statement", "Use Purpose Builder and save the final purpose statement.", "systems", "Purpose Builder", "Chapter 6", "purpose"),
        ("Review and Save Covenant", "Discuss the covenant line by line and save the approved covenant.", "systems", "Covenant Builder", "Chapter 7", "covenant"),
        ("Draft Rules", "Use Rules Builder to draft the Mutual Aid Society Agreement.", "systems", "Rules Builder", "Chapter 12", "rules"),
        ("Choose Meeting Rhythm", "Choose how often members meet and how decisions become records.", "people", "Meeting Builder", "Chapter 13", "meeting_rhythm"),
        ("Schedule First Meeting", "Generate and save the first meeting agenda, facilitator, recordkeeper, and next meeting date.", "people", "Meeting Builder", "Chapter 13", "first_meeting"),
    ],
    "Organize Operations": [
        ("Complete Treasury Setup", "Select contribution model, treasurer, assistant treasurer, approval rule, reserve rule, and reporting rhythm.", "systems", "Treasury Setup", "Chapter 8", "treasury_setup"),
        ("Define Contribution Rhythm", "Create a contribution rhythm the society can keep without shame or confusion.", "systems", "Treasury Setup", "Chapter 8", "contribution_rhythm"),
        ("Create Needs Map", "Map recurring needs by urgency, frequency, and solvability.", "community_impact", "Needs Map", "Chapter 10", "needs_map"),
        ("Create Skills and Assets Map", "Identify existing capacity before assuming scarcity.", "community_impact", "Skills and Assets Map", "Appendix K", "skills_assets_map"),
        ("Create Care Teams", "Create at least one care team with a lead, members, linked need, status, and notes.", "people", "Care Teams", "Chapter 11", "care_teams"),
        ("Invite members to complete Institutional Profiles", "Ask members to record contributions, skills, needs privacy, and current projects.", "people", "Institutional Profile", "Appendix K", "institutional_profiles"),
    ],
    "Complete First Action": [
        ("Choose First Action", "Choose one small, real, measurable action.", "projects", "First Action Tracker", "Appendix L", "first_action_choose"),
        ("Assign First Action Lead", "Name the project lead and members assigned.", "projects", "First Action Tracker", "Appendix L", "first_action_lead"),
        ("Prepare First Action", "Set date, resources, money needed, privacy level, and success measure.", "projects", "First Action Tracker", "Appendix L", "first_action_prepare"),
        ("Execute First Action", "Complete the action and record what happened.", "projects", "First Action Tracker", "Week 11", "first_action_execute"),
        ("Record Results", "Record who was served or supported, money used, what worked, what broke, and what must change.", "systems", "First Action Tracker", "Week 12", "first_action_record"),
    ],
    "Generate Day 100 Report": [
        ("Gather meeting notes", "Collect meeting decisions, assignments, records, and next steps.", "systems", "Day 100 Report", "Chapter 21", "gather_meeting_notes"),
        ("Gather ledger/treasury summary if available", "Collect contribution totals, aid distributed, balance, reserve, and report dates if available.", "systems", "Day 100 Report", "Chapter 21", "gather_treasury"),
        ("Gather care team activity", "Collect care team activity and lessons learned.", "people", "Day 100 Report", "Chapter 21", "gather_care"),
        ("Gather first action results", "Collect the First Action results and after-action review.", "projects", "Day 100 Report", "Chapter 21", "gather_first_action"),
        ("Generate Day 100 Report", "Generate the report with the required closing: We have not built everything. We have built the first container.", "systems", "Day 100 Report", "Chapter 21", "day_100_report"),
        ("Save Next Phase recommendation", "Choose one next-phase goal, first 30-day action, first 90-day goal, roles, resources, risks, and review date.", "projects", "Next Phase Planner", "Chapter 23", "next_phase"),
    ],
}


def _today():
    from datetime import date
    return date.today()


def sync_first_container_tasks(db: Session, society: Society, container=None) -> None:
    from app.models import SocietyContainer, SocietyTrustTask
    container = container or db.query(SocietyContainer).filter_by(society_id=society.id, container_type=FIRST_CONTAINER_TYPE, status="active").first()
    if not container:
        return
    tasks = db.query(SocietyTrustTask).filter_by(container_id=container.id).all()
    latest_audit = db.query(SocietyBlueprintAudit).filter_by(society_id=society.id).first()
    latest_purpose = db.query(SocietyPurpose).filter_by(society_id=society.id).first()
    active_cov = db.query(SocietyCovenant).filter_by(society_id=society.id, status="Active").first()
    first_ten = first_ten_summary(db, society.id)
    members = db.query(SocietyFirstTenMember).filter_by(society_id=society.id).all()
    roles = {m.role for m in members}
    complete_titles = set()
    if latest_audit:
        complete_titles |= {"Complete Blueprint Audit", "Identify weakest foundation area"}
    if society.id:
        complete_titles.add("Create Society")
    if first_ten["total"] >= 10:
        complete_titles.add("Name Your First Ten")
    if first_ten["total"] >= 3:
        complete_titles.add("Add at least 3 founding members")
    if first_ten["critical_role_completion"] >= 1:
        complete_titles.add("Fill at least 1 critical role")
    role_map = {"Facilitator": "Assign Facilitator", "Recordkeeper": "Assign Recordkeeper", "Treasurer": "Assign Treasurer", "Assistant Treasurer": "Assign Assistant Treasurer", "Care Coordinator": "Assign Care Coordinator"}
    for role, title in role_map.items():
        if role in roles:
            complete_titles.add(title)
    if latest_purpose:
        complete_titles |= {"Save Purpose Statement", "Choose first focus"}
    if active_cov:
        complete_titles.add("Review and Save Covenant")
    now = datetime.utcnow()
    for task in tasks:
        if task.title in complete_titles and task.status != "completed":
            task.status = "completed"
            task.completed_at = now
            task.completion_notes = task.completion_notes or "Completed from Society Builder activity sync."


def recalculate_container_progress(db: Session, container) -> None:
    from app.models import SocietyContainerMilestone, SocietyTrustTask
    sync_first_container_tasks(db, db.query(Society).filter_by(id=container.society_id).one(), container)
    tasks = db.query(SocietyTrustTask).filter_by(container_id=container.id).all()
    completed = sum(1 for t in tasks if t.status == "completed")
    container.percent_complete = round((completed / len(tasks)) * 100) if tasks else 0
    if container.start_date:
        days = (_today() - container.start_date).days + 1
        container.current_day = max(1, min(100, days))
        container.current_week = max(1, min(15, ((container.current_day - 1) // 7) + 1))
    milestones = db.query(SocietyContainerMilestone).filter_by(container_id=container.id).order_by(SocietyContainerMilestone.sequence_order).all()
    active = None
    for m in milestones:
        mtasks = [t for t in tasks if t.milestone_id == m.id]
        if mtasks and all(t.status == "completed" for t in mtasks):
            m.status = "completed"
        elif mtasks and any(t.status in {"this_week", "in_progress", "waiting", "completed"} for t in mtasks):
            m.status = "in_progress"
        else:
            m.status = "not_started"
        if active is None and m.status != "completed":
            active = m
    if active:
        active.status = "in_progress" if active.status == "not_started" else active.status
        container.active_milestone_id = active.id
    elif milestones:
        container.active_milestone_id = milestones[-1].id
        container.status = "completed"


def activate_first_container(db: Session, society: Society, actor_user_id: int | None):
    from datetime import timedelta
    from app.models import SocietyContainer, SocietyContainerMilestone, SocietyTrustTask
    existing = db.query(SocietyContainer).filter_by(society_id=society.id, container_type=FIRST_CONTAINER_TYPE, status="active").first()
    if existing:
        recalculate_container_progress(db, existing)
        return existing
    start = _today()
    container = SocietyContainer(society_id=society.id, container_type=FIRST_CONTAINER_TYPE, title=FIRST_CONTAINER_TITLE, description="Help a new society build the first trustworthy container: gather, decide, contribute, record, care, report, and return.", status="active", start_date=start, target_end_date=start + timedelta(days=99), current_day=1, current_week=1, created_by=actor_user_id)
    db.add(container); db.flush()
    milestone_by_title = {}
    for i, (title, desc, phase, weight) in enumerate(FIRST_CONTAINER_MILESTONE_TEMPLATES, 1):
        m = SocietyContainerMilestone(container_id=container.id, title=title, description=desc, sequence_order=i, phase_label=phase, percent_weight=weight, status="not_started")
        db.add(m); db.flush(); milestone_by_title[title] = m
    for milestone_title, rows in FIRST_CONTAINER_TASK_TEMPLATES.items():
        m = milestone_by_title[milestone_title]
        for idx, (title, desc, lane, module, chapter, step) in enumerate(rows, 1):
            status = "this_week" if m.sequence_order == 1 else "backlog"
            db.add(SocietyTrustTask(society_id=society.id, container_id=container.id, milestone_id=m.id, title=title, description=desc, status=status, lane=lane, task_type="container_step", linked_module=module, linked_handbook_chapter=chapter, linked_container_step=step, priority="high" if idx == 1 else "normal", created_from_template=True, created_by=actor_user_id))
    recalculate_container_progress(db, container)
    audit(db, actor_user_id=actor_user_id, action="first_container_activated", entity_id=society.id, after={"container_id": container.id, "title": container.title})
    return container


def container_dict(db: Session, container) -> dict:
    from app.models import SocietyContainerMilestone, SocietyTrustTask
    recalculate_container_progress(db, container)
    milestones = db.query(SocietyContainerMilestone).filter_by(container_id=container.id).order_by(SocietyContainerMilestone.sequence_order).all()
    tasks = db.query(SocietyTrustTask).filter_by(container_id=container.id).all()
    active = next((m for m in milestones if m.id == container.active_milestone_id), None)
    data = _row_dict(container)
    data["milestones"] = [_row_dict(m) for m in milestones]
    data["active_milestone"] = _row_dict(active)
    data["task_counts"] = {status: sum(1 for t in tasks if t.status == status) for status in TRUST_TASK_STATUSES}
    data["this_week_tasks"] = [_row_dict(t) for t in tasks if t.status == "this_week"][:10]
    data["blocked_tasks"] = [_row_dict(t) for t in tasks if t.status == "waiting"][:10]
    return data


def task_dict(task) -> dict:
    return _row_dict(task)
