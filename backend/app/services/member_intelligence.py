from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    LeadershipAssessment,
    MemberProfile,
    Society,
    SocietyFirstTenMember,
    SocietyInstitutionalProfile,
    SocietyMembership,
    SocietyRoleAppointmentHistory,
    SocietyRoleCandidateReview,
    SocietyRoleOpening,
)

OFFICIAL_ASSESSMENT_TITLES = [
    "Business Owner Assessment",
    "Customer / Voice of Customer",
    "Love Archetype Engine",
    "Leadership Archetype Engine",
    "Loyalty Archetype Engine",
    "Youth Rite of Passage / Gates",
    "K–6 Assessment MVP",
]

STATIC_BEHAVIORAL_PROFILES_STATUS = "deprecated_fallback_only"


def _source(system: str, row: Any | None = None, summary: str = "") -> dict[str, Any]:
    return {
        "system": system,
        "model": row.__class__.__name__ if row is not None else None,
        "id": getattr(row, "id", None),
        "summary": summary,
    }


def _safe_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text or "{}")
        return value if isinstance(value, dict) else {"value": value}
    except (TypeError, ValueError):
        return {"raw": text}


def _profile_assessment_records(profile: MemberProfile | None) -> list[dict[str, Any]]:
    growth = (profile.attributes or {}).get("growth_profile", {}) if profile else {}
    records: list[dict[str, Any]] = []
    for category, category_payload in (growth.get("categories") or {}).items():
        for assessment in (category_payload.get("assessments") or {}).values():
            if isinstance(assessment, dict):
                records.append({**assessment, "category": category, "source": "Garvey assessments"})
    return records


def _leadership_assessment_record(row: LeadershipAssessment) -> dict[str, Any]:
    scores = _safe_json(row.scores)
    return {
        "assessment_id": str(row.id),
        "assessment_name": "Member Leadership Assessment",
        "category": "member assessment",
        "completion_date": row.created_at.isoformat() if row.created_at else None,
        "strengths": scores.get("strengths") or [],
        "opportunities_for_growth": scores.get("growth_areas") or scores.get("opportunities_for_growth") or [],
        "source": "member assessments",
    }


def _assessment_name(record: dict[str, Any]) -> str:
    return str(record.get("assessment_name") or record.get("assessment_id") or record.get("category") or "Assessment")


def generate_member_intelligence(db: Session, *, society_id: int, member_id: int) -> dict[str, Any]:
    """Build a generated, read-only member intelligence profile from existing society data."""
    society = db.query(Society).filter(Society.id == society_id).first()
    membership = db.query(SocietyMembership).filter_by(society_id=society_id, user_id=member_id).first()
    profile = db.query(MemberProfile).filter_by(user_id=member_id).first()
    first_ten = db.query(SocietyFirstTenMember).filter_by(society_id=society_id, user_id=member_id).first()
    institutional = db.query(SocietyInstitutionalProfile).filter_by(society_id=society_id, user_id=member_id).first()
    leadership_rows = db.query(LeadershipAssessment).filter_by(user_id=member_id).order_by(LeadershipAssessment.created_at.desc()).all()

    evidence_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    strengths: list[str] = []
    development: list[str] = []
    archetypes: list[str] = []

    if society:
        evidence_sources.append(_source("Society", society, society.name))
    if membership:
        evidence_sources.append(_source("SocietyMembership", membership, f"Active role: {membership.role}"))
    else:
        warnings.append("No SocietyMembership record was found for this member in this society.")
    if profile:
        evidence_sources.append(_source("member profile", profile, "Member profile attributes included."))
        attrs = profile.attributes or {}
        archetypes.extend([str(v) for v in attrs.get("archetypes", []) if v])
    else:
        warnings.append("No member profile data is available yet.")

    assessment_records = _profile_assessment_records(profile) + [_leadership_assessment_record(row) for row in leadership_rows]
    for row in leadership_rows:
        evidence_sources.append(_source("member assessments", row, "Leadership assessment submission."))
    for record in assessment_records:
        strengths.extend(str(item) for item in record.get("strengths") or [] if item)
        development.extend(str(item) for item in record.get("opportunities_for_growth") or [] if item)
        primary = record.get("primary_result") or record.get("archetype") or record.get("category")
        if isinstance(primary, dict):
            primary = primary.get("name") or primary.get("title")
        if primary:
            archetypes.append(str(primary))

    official_titles = OFFICIAL_ASSESSMENT_TITLES
    completed_names = {_assessment_name(record) for record in assessment_records}
    completed_categories = {str(record.get("category")) for record in assessment_records if record.get("category")}
    missing_assessments = [title for title in official_titles if title not in completed_names and title not in completed_categories]
    if not assessment_records:
        warnings.append("No Garvey or member assessment evidence is available; confidence is limited.")

    considered_roles: list[dict[str, Any]] = []
    if first_ten:
        evidence_sources.append(_source("First Ten", first_ten, f"Considered role: {first_ten.role}"))
        considered_roles.append({"role": first_ten.role, "status": first_ten.status, "evidence": first_ten.possible_contribution or first_ten.notes})
        if first_ten.reliability_score >= 4:
            strengths.append("Reliability")
        if first_ten.confidentiality_score >= 4:
            strengths.append("Confidentiality")
        if first_ten.relationship_capacity_score >= 4:
            strengths.append("Relationship capacity")
        if first_ten.skill_capacity_score >= 4:
            strengths.append("Skill capacity")
        if first_ten.possible_contribution:
            strengths.append(first_ten.possible_contribution)
        if first_ten.notes:
            evidence_sources.append(_source("First Ten notes", first_ten, first_ten.notes))
    else:
        warnings.append("No linked First Ten entry was found for this member.")

    if institutional:
        evidence_sources.append(_source("institutional profile", institutional, institutional.primary_contribution or institutional.headline))
        if institutional.primary_contribution:
            strengths.append(institutional.primary_contribution)
        development.extend(str(item) for item in (institutional.skills_to_learn_json or []) if item)

    reviews = db.query(SocietyRoleCandidateReview).filter_by(society_id=society_id).all()
    if first_ten:
        reviews = [review for review in reviews if review.candidate_member_id == first_ten.id]
    else:
        reviews = []
    role_alignment_summaries = []
    for review in reviews:
        opening = db.query(SocietyRoleOpening).filter_by(id=review.role_opening_id).first()
        evidence_sources.append(_source("role candidate reviews", review, review.alignment_label))
        considered_roles.append({"role": opening.title if opening else "Role opening", "status": review.decision, "alignment_label": review.alignment_label})
        role_alignment_summaries.append({"role": opening.title if opening else "Role opening", "alignment_label": review.alignment_label, "confidence": review.behavioral_confidence, "supporting_evidence": review.behavioral_evidence})

    history = db.query(SocietyRoleAppointmentHistory).filter_by(society_id=society_id).order_by(SocietyRoleAppointmentHistory.created_at.desc()).all()
    if first_ten:
        history = [row for row in history if row.candidate_member_id == first_ten.id]
    else:
        history = []
    past_roles = []
    for row in history:
        evidence_sources.append(_source("role assignment history", row, row.role_title))
        past_roles.append({"role": row.role_title, "reason": row.reason, "training_status": row.training_status})

    evidence_count = len(evidence_sources)
    confidence = "substantial" if assessment_records and first_ten and (reviews or history or institutional) else "developing" if evidence_count >= 3 else "limited"
    return {
        "member_id": member_id,
        "society_id": society_id,
        "completed_assessments": sorted(completed_names),
        "missing_assessments": missing_assessments,
        "archetypes": sorted(set(archetypes)),
        "behavioral_strengths": sorted(set(strengths)),
        "development_areas": sorted(set(development)),
        "current_roles": [membership.role] if membership else [],
        "considered_roles": considered_roles,
        "past_roles": past_roles,
        "role_alignment_summaries": role_alignment_summaries,
        "confidence_level": confidence,
        "evidence_sources": evidence_sources,
        "warnings": warnings,
        "static_behavioral_profiles": STATIC_BEHAVIORAL_PROFILES_STATUS,
        "software_boundary": "Read-only generated intelligence; no automatic appointments are created.",
    }
