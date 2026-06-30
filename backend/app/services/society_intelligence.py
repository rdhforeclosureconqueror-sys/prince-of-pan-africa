from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models import LeadershipAssessment, MemberProfile, Society, SocietyBlueprintAudit, SocietyContainer, SocietyCovenant, SocietyFirstTenMember, SocietyInstitutionalProfile, SocietyMembership, SocietyPurpose, SocietyRoleAppointmentHistory, SocietyRoleCandidateReview, SocietyRoleOpening, SocietyTrustTask
from app.services.member_intelligence import OFFICIAL_ASSESSMENT_TITLES, generate_member_intelligence

CRITICAL_ROLES = ["Facilitator", "Treasurer", "Assistant Treasurer", "Recordkeeper", "Care Coordinator"]


def _src(system: str, rows: list[Any], summary: str) -> dict[str, Any]:
    return {"system": system, "models": sorted({r.__class__.__name__ for r in rows if r is not None}), "ids": [getattr(r, "id", None) for r in rows if r is not None], "summary": summary}


def _score(name: str, value: int, evidence: list[str], calculation: str, confidence: str, missing: list[str]) -> dict[str, Any]:
    return {"name": name, "score": max(0, min(100, round(value))), "why": "; ".join(evidence) if evidence else "No usable evidence found.", "evidence": evidence, "calculation": calculation, "confidence": confidence, "missing_evidence": missing}


def _pct(done: int, total: int) -> int:
    return round((done / total) * 100) if total else 0


def _confidence(present: int, total: int) -> str:
    ratio = present / total if total else 0
    if ratio >= .75:
        return "substantial"
    if ratio >= .45:
        return "developing"
    return "limited"


def _avg_first_ten(rows: list[SocietyFirstTenMember], fields: list[str]) -> int:
    vals = [getattr(r, f) for r in rows for f in fields]
    return round(((mean(vals) if vals else 0) / 5) * 100) if vals else 0


def generate_society_intelligence(db: Session, *, society_id: int, include_debug: bool = False) -> dict[str, Any]:
    society = db.query(Society).filter(Society.id == society_id).first()
    if not society:
        raise ValueError("Society not found")
    memberships = db.query(SocietyMembership).filter_by(society_id=society_id, status="active").all()
    first_ten = db.query(SocietyFirstTenMember).filter_by(society_id=society_id).all()
    profiles = db.query(SocietyInstitutionalProfile).filter_by(society_id=society_id).all()
    openings = db.query(SocietyRoleOpening).filter_by(society_id=society_id).all()
    reviews = db.query(SocietyRoleCandidateReview).filter_by(society_id=society_id).all()
    appointments = db.query(SocietyRoleAppointmentHistory).filter_by(society_id=society_id).all()
    blueprint = db.query(SocietyBlueprintAudit).filter_by(society_id=society_id).order_by(SocietyBlueprintAudit.created_at.desc(), SocietyBlueprintAudit.id.desc()).first()
    purpose = db.query(SocietyPurpose).filter_by(society_id=society_id).order_by(SocietyPurpose.created_at.desc(), SocietyPurpose.id.desc()).first()
    covenant = db.query(SocietyCovenant).filter_by(society_id=society_id).order_by(SocietyCovenant.created_at.desc(), SocietyCovenant.id.desc()).first()
    container = db.query(SocietyContainer).filter_by(society_id=society_id, status="active").order_by(SocietyContainer.created_at.desc(), SocietyContainer.id.desc()).first()
    tasks = db.query(SocietyTrustTask).filter_by(society_id=society_id).all()
    linked_user_ids = [m.user_id for m in memberships]
    member_profiles = db.query(MemberProfile).filter(MemberProfile.user_id.in_(linked_user_ids or [-1])).all()
    assessments = db.query(LeadershipAssessment).filter(LeadershipAssessment.user_id.in_(linked_user_ids or [-1])).all()
    member_intel = [generate_member_intelligence(db, society_id=society_id, member_id=uid) for uid in linked_user_ids]

    sources = [_src("Society", [society], society.name), _src("Member Intelligence", memberships, "Generated live from active memberships; members remain source of truth for individuals.")]
    for name, rows in [("First Ten", first_ten), ("Institutional Profiles", profiles), ("Role Openings", openings), ("Role Candidate Reviews", reviews), ("Role Appointment History", appointments), ("Blueprint Audit", [blueprint] if blueprint else []), ("Purpose", [purpose] if purpose else []), ("Covenant", [covenant] if covenant else []), ("Trust Board", tasks), ("Member/Garvey assessments", assessments + member_profiles)]:
        if rows:
            sources.append(_src(name, rows, f"{len(rows)} existing record(s) read."))

    role_names = {r.role for r in first_ten if r.role} | {m.role for m in memberships if m.role} | {a.role_title for a in appointments if a.role_title}
    missing_roles = [r for r in CRITICAL_ROLES if r not in role_names]
    covered_critical = len(CRITICAL_ROLES) - len(missing_roles)
    profile_users = {p.user_id for p in profiles}
    completed_member_assessments = sum(1 for mi in member_intel if mi["completed_assessments"])
    trust_values = []
    if blueprint:
        trust_values.append((blueprint.trust_score / 5) * 100)
    if first_ten:
        trust_values.append(_avg_first_ten(first_ten, ["reliability_score", "confidentiality_score", "relationship_capacity_score"]))
    if tasks:
        trust_values.append(_pct(len([t for t in tasks if t.status == "completed"]), len(tasks)))

    scores = {}
    scores["trust_score"] = _score("Trust Score", round(mean(trust_values)) if trust_values else 0, [f"Blueprint trust={blueprint.trust_score}/5" if blueprint else "No blueprint trust score", f"First Ten trust signals from {len(first_ten)} people", f"Trust Board completed {len([t for t in tasks if t.status == 'completed'])}/{len(tasks)} tasks"], "Average available trust signals: blueprint trust, First Ten reliability/confidentiality/relationship capacity, and completed Trust Board work.", _confidence(len(trust_values), 3), [x for x, ok in [("Blueprint Audit trust_score", blueprint), ("First Ten trust scores", first_ten), ("Trust Board activity", tasks)] if not ok])
    scores["participation_score"] = _score("Participation Score", round(mean([_pct(len(memberships), max(10, len(memberships))), _pct(len(profiles), max(1, len(memberships))), _pct(len([t for t in tasks if t.owner_member_id]), len(tasks) or 1)])), [f"{len(memberships)} active memberships", f"{len(profiles)} institutional profiles", f"{len([t for t in tasks if t.owner_member_id])} owned Trust Board tasks"], "Average of membership base toward First Ten threshold, institutional profile completion, and Trust Board ownership.", _confidence(sum(1 for x in [memberships, profiles, tasks] if x), 3), [])
    scores["leadership_coverage"] = _score("Leadership Coverage", _pct(covered_critical, len(CRITICAL_ROLES)), [f"Covered critical roles: {covered_critical}/{len(CRITICAL_ROLES)}", f"Missing roles: {', '.join(missing_roles) or 'none'}"], "Critical roles covered divided by required critical roles.", _confidence(len(role_names), len(CRITICAL_ROLES)), missing_roles)
    scores["assessment_completion"] = _score("Assessment Completion", _pct(completed_member_assessments, len(memberships)), [f"{completed_member_assessments}/{len(memberships)} active members have Member Intelligence assessment evidence", f"Official assessment catalog has {len(OFFICIAL_ASSESSMENT_TITLES)} expected titles"], "Members with at least one Garvey/member assessment divided by active members.", _confidence(completed_member_assessments, len(memberships)), ["Garvey/member assessment evidence" ] if completed_member_assessments < len(memberships) else [])
    scores["role_coverage"] = _score("Role Coverage", _pct(len([o for o in openings if o.status in {"open", "appointed"}]) + len(appointments), max(len(CRITICAL_ROLES), len(openings) or 1)), [f"{len(openings)} role openings", f"{len(appointments)} appointment history records"], "Open or appointed role structures plus recorded appointments over expected role need.", _confidence(len(openings)+len(appointments), len(CRITICAL_ROLES)), missing_roles)
    scores["knowledge_coverage"] = _score("Knowledge Coverage", _pct(len([t for t in tasks if t.linked_handbook_chapter or t.source_reader_path]), len(tasks) or 1), [f"{len([t for t in tasks if t.linked_handbook_chapter or t.source_reader_path])}/{len(tasks)} Trust Board tasks link to handbook/Knowledge Commons references"], "Linked knowledge tasks divided by Trust Board tasks.", _confidence(len(tasks), 1), ["Knowledge Commons/handbook task links"] if not tasks else [])
    business_base = [blueprint.businesses_score if blueprint else 0, len([p for p in profiles if p.current_projects_json or p.contribution_type != "Volunteer"]), len([o for o in openings if "business" in (o.title or "").lower()])]
    scores["business_readiness"] = _score("Business Readiness", round(mean([(business_base[0]/5)*100 if blueprint else 0, _pct(business_base[1], max(1, len(profiles))), 100 if business_base[2] else 0])), [f"Blueprint businesses score: {blueprint.businesses_score if blueprint else 'missing'}/5", f"{business_base[1]} profiles show projects or paid/pro organizer capacity", f"{business_base[2]} business role openings"], "Average of Blueprint business score, profile project/professional capacity, and business-specific role coverage.", _confidence(sum(1 for x in [blueprint, profiles, business_base[2]] if x), 3), ["Blueprint business score"] if not blueprint else [])
    scores["institution_readiness"] = _score("Institution Readiness", round(mean([100 if purpose else 0, 100 if covenant else 0, (blueprint.institutions_score/5)*100 if blueprint else 0, container.percent_complete if container else 0])), [f"Purpose {'complete' if purpose else 'missing'}", f"Covenant {'complete' if covenant else 'missing'}", f"Blueprint institutions score: {blueprint.institutions_score if blueprint else 'missing'}/5", f"First 100 Days progress: {container.percent_complete if container else 0}%"], "Average of purpose, covenant, Blueprint institutions score, and active container progress.", _confidence(sum(1 for x in [purpose, covenant, blueprint, container] if x), 4), [x for x, ok in [("Purpose", purpose), ("Covenant", covenant), ("Blueprint Audit", blueprint), ("First 100 Days Container", container)] if not ok])
    scores["first_100_days_progress"] = _score("First 100 Days Progress", container.percent_complete if container else 0, [f"Active container percent_complete={container.percent_complete}%" if container else "No active First 100 Days container"], "Uses existing SocietyContainer.percent_complete only; no workflow is activated.", _confidence(1 if container else 0, 1), ["Active First 100 Days Container"] if not container else [])
    scores["member_growth"] = _score("Member Growth", round(mean([_pct(len(memberships), 10), _pct(len(profile_users), len(memberships) or 1), _pct(len(member_profiles)+len(assessments), len(memberships) or 1)])), [f"{len(memberships)} active members", f"{len(profile_users)} profiles", f"{len(member_profiles)+len(assessments)} member profile/assessment records"], "Average of active membership toward First Ten, institutional profiles, and growth/assessment evidence.", _confidence(sum(1 for x in [memberships, profile_users, member_profiles or assessments] if x), 3), [])
    scores["volunteer_capacity"] = _score("Volunteer Capacity", round(mean([_pct(len([p for p in profiles if p.availability]), len(profiles) or 1), _pct(len([p for p in profiles if p.primary_contribution]), len(profiles) or 1), _avg_first_ten(first_ten, ["skill_capacity_score"])])), [f"{len([p for p in profiles if p.availability])} profiles include availability", f"{len([p for p in profiles if p.primary_contribution])} profiles include contribution", "First Ten skill capacity included when present"], "Average of availability, contribution clarity, and First Ten skill capacity.", _confidence(sum(1 for x in [profiles, first_ten] if x), 2), ["Institutional profile availability"] if not profiles else [])
    core = [scores[k]["score"] for k in ["trust_score", "participation_score", "leadership_coverage", "assessment_completion", "role_coverage", "knowledge_coverage", "business_readiness", "institution_readiness"]]
    scores["society_health_score"] = _score("Society Health Score", round(mean(core)), [f"Averaged {len(core)} explained domain scores"], "Mean of trust, participation, leadership, assessment, role, knowledge, business, and institution readiness scores.", _confidence(len(sources), 12), [])

    risks = [f"Missing critical role: {r}" for r in missing_roles] + [s["name"] + " lacks evidence" for s in scores.values() if s["confidence"] == "limited"]
    strengths = [s["name"] + f" is {s['score']} because {s['why']}" for s in scores.values() if s["score"] >= 70]
    missing = sorted({m for s in scores.values() for m in s["missing_evidence"]})
    recommended = [{"action": f"Address {r}", "why": f"Society Intelligence found this risk from existing evidence: {r}. This is a recommendation only; no workflow or appointment is created."} for r in risks[:6]] or [{"action": "Keep strengthening documented practice", "why": "Current evidence shows no urgent gap above threshold; continue completing assessments, roles, profiles, and Trust Board work."}]
    result = {"ok": True, "society_id": society_id, "society_name": society.name, "scores": scores, "overall_health": scores["society_health_score"], "top_risks": risks[:8], "top_strengths": strengths[:8], "missing_roles": missing_roles, "recommended_next_steps": recommended, "confidence": _confidence(len(sources), 12), "evidence_sources": sources, "warnings": ["Read-only generated model: it does not write records, create appointments, or execute workflows."] + (["Missing evidence lowers confidence: " + ", ".join(missing)] if missing else []), "missing_information": missing, "software_boundary": "Society Intelligence reads existing evidence only. Member Intelligence remains the source of truth for individuals.", "debug": None}
    if include_debug:
        result["debug"] = {"raw_society_intelligence_json": {k: v for k, v in result.items() if k != "debug"}, "score_calculations": scores, "evidence_sources": sources, "confidence_calculation": "Confidence is based on how many expected evidence families are present.", "fallback_reasons": [w for w in result["warnings"] if "Missing" in w], "missing_evidence": missing}
    return result
