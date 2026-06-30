from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models import LeadershipAssessment, MemberProfile, Society, SocietyInstitutionalProfile, SocietyMembership, SocietyTrustTask
from app.services.institution_intelligence import generate_institution_intelligence
from app.services.member_intelligence import generate_member_intelligence
from app.services.society_intelligence import CRITICAL_ROLES, generate_society_intelligence

EXPANDED_ROLES = ["Treasurer", "Secretary", "Historian", "Membership Chair", "Education Chair", "Finance Chair", *CRITICAL_ROLES]
READ_ONLY_WARNING = "Read-only generated model: Opportunity Intelligence does not write records, execute workflows, create appointments, assign members, schedule appointments, create tasks, or send notifications."


def _confidence_label(score: int) -> str:
    return "substantial" if score >= 75 else "developing" if score >= 45 else "limited"


def _priority(score: int) -> str:
    return "high" if score >= 75 else "medium" if score >= 50 else "low"


def _score(parts: dict[str, int]) -> tuple[int, str]:
    value = round(mean(parts.values())) if parts else 0
    why = "; ".join(f"{k}={v}" for k, v in parts.items()) + f"; mean={value}"
    return value, why


def _opp(*, oid: str, title: str, typ: str, parts: dict[str, int], action: str, reason: str, evidence: list[str], missing: list[str] | None = None, members: list[int] | None = None, roles: list[str] | None = None, containers: list[int] | None = None, societies: list[int] | None = None, institutions: list[int] | None = None, manual: bool = True) -> dict[str, Any]:
    score, calc = _score(parts)
    return {
        "id": oid,
        "title": title,
        "type": typ,
        "priority": _priority(score),
        "priority_score": score,
        "confidence": _confidence_label(round(mean([score, min(100, len(evidence) * 20), 100 - min(80, len(missing or []) * 20)]))),
        "impact": parts.get("impact", score),
        "effort": parts.get("effort", 50),
        "recommended_action": action,
        "reason": reason,
        "priority_calculation": calc,
        "evidence": evidence,
        "missing_evidence": missing or [],
        "related_members": members or [],
        "related_roles": roles or [],
        "related_containers": containers or [],
        "related_societies": societies or [],
        "related_institutions": institutions or [],
        "requires_manual_review": manual,
        "no_workflow_executed": True,
    }


def generate_opportunity_intelligence(db: Session, *, society_id: int | None = None, include_debug: bool = False) -> dict[str, Any]:
    societies = db.query(Society).filter(Society.id == society_id).all() if society_id else db.query(Society).order_by(Society.id).all()
    if society_id and not societies:
        raise ValueError("Society not found")
    opportunities: list[dict[str, Any]] = []
    evidence_sources: list[str] = []
    missing_all: set[str] = set()
    debug_payload: dict[str, Any] = {"societies": []}

    for society in societies:
        si = generate_society_intelligence(db, society_id=society.id, include_debug=include_debug)
        ii = generate_institution_intelligence(db, institution_id=society.id, include_debug=include_debug)
        scores = si["scores"]
        evidence_sources += [f"Society {society.id}: {e['system']} — {e['summary']}" for e in si.get("evidence_sources", [])]
        missing_all.update(si.get("missing_information", [])); missing_all.update(ii.get("missing_evidence", []))
        memberships = db.query(SocietyMembership).filter_by(society_id=society.id, status="active").all()
        profiles = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id).all()
        tasks = db.query(SocietyTrustTask).filter_by(society_id=society.id).all()
        user_ids = [m.user_id for m in memberships]
        assessments = db.query(LeadershipAssessment).filter(LeadershipAssessment.user_id.in_(user_ids or [-1])).all()
        member_profiles = db.query(MemberProfile).filter(MemberProfile.user_id.in_(user_ids or [-1])).all()
        role_names = {m.role for m in memberships if m.role}
        missing_roles = [r for r in EXPANDED_ROLES if r not in role_names and r not in si.get("missing_roles", [])] + si.get("missing_roles", [])
        missing_roles = list(dict.fromkeys(missing_roles))
        for role in missing_roles:
            opportunities.append(_opp(oid=f"society-{society.id}-missing-role-{role.lower().replace(' ', '-')}", title=f"Recruit or confirm {role}", typ="role", parts={"impact": 85, "confidence": scores["role_coverage"]["score"], "readiness": 100 - scores["role_coverage"]["score"], "effort": 45}, action=f"Manually review candidates and recruit a {role}; do not appoint automatically.", reason=f"Role coverage evidence indicates {role} is not covered.", evidence=scores["role_coverage"].get("evidence", []), missing=[role], roles=[role], societies=[society.id]))
        if si.get("missing_roles") and scores["leadership_coverage"]["score"] < 100:
            candidate_ids = [p.user_id for p in profiles if p.primary_contribution or p.current_projects_json]
            opportunities.append(_opp(oid=f"society-{society.id}-leadership-candidates", title="Review leadership candidates for vacant roles", typ="leadership", parts={"impact": 90, "confidence": scores["leadership_coverage"]["score"], "trust": scores["trust_score"]["score"], "assessment_completion": scores["assessment_completion"]["score"], "effort": 55}, action="Manually review high-trust members against vacant leadership roles.", reason="Leadership roles are vacant and member/profile evidence exists for human candidate review.", evidence=scores["leadership_coverage"].get("evidence", []) + scores["trust_score"].get("evidence", []), missing=si.get("missing_roles", []), members=candidate_ids, roles=si.get("missing_roles", []), societies=[society.id]))
        incomplete_members = [m.user_id for m in memberships if m.user_id not in {a.user_id for a in assessments} and m.user_id not in {p.user_id for p in member_profiles}]
        if incomplete_members or scores["assessment_completion"]["score"] < 70:
            opportunities.append(_opp(oid=f"society-{society.id}-assessment-completion", title="Complete missing member assessments", typ="assessment", parts={"impact": 70, "confidence": scores["assessment_completion"]["score"], "readiness": 100 - scores["assessment_completion"]["score"], "effort": 35}, action="Invite members to complete assessments manually; do not change profiles automatically.", reason="Assessment evidence is incomplete, lowering confidence in recommendations.", evidence=scores["assessment_completion"].get("evidence", []), missing=scores["assessment_completion"].get("missing_evidence", []), members=incomplete_members, societies=[society.id]))
        open_tasks = [t for t in tasks if t.status not in {"completed", "done"} and not t.owner_member_id]
        available = [p for p in profiles if p.availability]
        if open_tasks and available:
            opportunities.append(_opp(oid=f"society-{society.id}-volunteer-match", title="Match available volunteers to open Trust Board work", typ="volunteer", parts={"impact": 75, "confidence": scores["volunteer_capacity"]["score"], "participation": scores["participation_score"]["score"], "effort": 40}, action="Manually ask available members whether they want to volunteer for open work.", reason="Open tasks and member availability exist, but no assignment is made.", evidence=scores["volunteer_capacity"].get("evidence", []) + [f"{len(open_tasks)} open unowned Trust Board tasks"], members=[p.user_id for p in available], societies=[society.id]))
        if len(profiles) >= 2:
            opportunities.append(_opp(oid=f"society-{society.id}-mentorship", title="Consider mentorship pairs", typ="mentorship", parts={"impact": 65, "confidence": scores["assessment_completion"]["score"], "participation": scores["participation_score"]["score"], "effort": 45}, action="Manually review experienced and newer members for mentorship fit.", reason="Multiple profiles provide strengths, learning goals, or needs for human mentorship review.", evidence=[f"{len(profiles)} institutional profiles available"], missing=[] if assessments else ["Leadership/member assessments for stronger matching"], members=[p.user_id for p in profiles], societies=[society.id]))
        if scores["business_readiness"]["score"] >= 60:
            opportunities.append(_opp(oid=f"society-{society.id}-business-incubation", title="Evaluate business incubation readiness", typ="business", parts={"impact": 90, "confidence": scores["business_readiness"]["score"], "trust": scores["trust_score"]["score"], "leadership": scores["leadership_coverage"]["score"], "effort": 70}, action="Convene manual business incubation review.", reason="Business readiness, trust, and leadership evidence suggest a possible incubation opportunity.", evidence=scores["business_readiness"].get("evidence", []), missing=scores["business_readiness"].get("missing_evidence", []), members=[p.user_id for p in profiles if p.current_projects_json], societies=[society.id]))
        if scores["trust_score"]["score"] < 60:
            opportunities.append(_opp(oid=f"society-{society.id}-trust-building", title="Prioritize trust-building activities", typ="trust", parts={"impact": 80, "confidence": scores["trust_score"]["score"], "readiness": 100 - scores["trust_score"]["score"], "effort": 50}, action="Manually plan trust-building conversations and record completion evidence later.", reason="Trust score is below healthy threshold or lacks evidence.", evidence=scores["trust_score"].get("evidence", []), missing=scores["trust_score"].get("missing_evidence", []), societies=[society.id]))
        if scores["knowledge_coverage"]["score"] < 60:
            opportunities.append(_opp(oid=f"society-{society.id}-education", title="Strengthen education and knowledge coverage", typ="education", parts={"impact": 65, "confidence": scores["knowledge_coverage"]["score"], "readiness": 100 - scores["knowledge_coverage"]["score"], "effort": 35}, action="Recommend learning modules for manual selection.", reason="Knowledge coverage or assessment completion is low.", evidence=scores["knowledge_coverage"].get("evidence", []), missing=scores["knowledge_coverage"].get("missing_evidence", []), societies=[society.id]))
        if scores["first_100_days_progress"]["score"] >= 90 and scores["trust_score"]["score"] >= 70 and scores["leadership_coverage"]["score"] >= 70:
            opportunities.append(_opp(oid=f"society-{society.id}-growth-container", title="Consider launching the next container", typ="society_growth", parts={"impact": 85, "confidence": scores["first_100_days_progress"]["score"], "trust": scores["trust_score"]["score"], "leadership": scores["leadership_coverage"]["score"], "effort": 65}, action="Manually decide whether to launch the next container.", reason="First Ten/container, trust, and leadership health appear strong.", evidence=scores["first_100_days_progress"].get("evidence", []) + scores["trust_score"].get("evidence", []), societies=[society.id]))
        if ii["institution_health"]["score"] >= 75:
            opportunities.append(_opp(oid=f"society-{society.id}-institution-formation", title="Consider institution formation", typ="institution", parts={"impact": 95, "confidence": ii["institution_health"]["score"], "readiness": ii["scores"]["operational_readiness"]["score"], "effort": 80}, action="Manually review institution formation readiness.", reason="Institution Intelligence health and operational readiness are strong.", evidence=ii["institution_health"].get("evidence", []), missing=ii.get("missing_evidence", []), societies=[society.id], institutions=[society.id]))
        contributors = [p.user_id for p in profiles if p.impact_summary_json or p.primary_contribution]
        if contributors and scores["participation_score"]["score"] >= 50:
            opportunities.append(_opp(oid=f"society-{society.id}-recognition", title="Recognize sustained member contribution", typ="recognition", parts={"impact": 55, "confidence": scores["participation_score"]["score"], "readiness": scores["trust_score"]["score"], "effort": 25}, action="Manually consider recognition for documented contribution.", reason="Contribution and participation evidence indicate members may merit recognition.", evidence=scores["participation_score"].get("evidence", []), members=contributors, societies=[society.id]))
        if include_debug:
            debug_payload["societies"].append({"society_intelligence": si, "institution_intelligence": ii})

    opportunities.sort(key=lambda o: (-o["priority_score"], o["type"], o["id"]))
    overall = round(mean([o["priority_score"] for o in opportunities[:10]])) if opportunities else 0
    buckets = {level: [o for o in opportunities if o["priority"] == level] for level in ["high", "medium", "low"]}
    by_type = {typ: [o for o in opportunities if o["type"] == typ] for typ in sorted({o["type"] for o in opportunities})}
    result = {
        "ok": True,
        "overall_priority": {"score": overall, "label": _priority(overall), "why": "Mean of the top ten deterministic opportunity priority scores."},
        "confidence": _confidence_label(round(mean([min(100, len(evidence_sources) * 8), 100 - min(80, len(missing_all) * 5), overall])) if opportunities else 0),
        "evidence": evidence_sources,
        "missing_evidence": sorted(missing_all),
        "recommendations": [{"action": o["recommended_action"], "why": o["reason"], "opportunity_id": o["id"]} for o in opportunities[:8]],
        "warnings": [READ_ONLY_WARNING, "All recommendations require human review; no workflow was executed."],
        "opportunities": opportunities,
        "dashboard": {"top_opportunities": opportunities[:10], "high_priority": buckets["high"], "medium_priority": buckets["medium"], "low_priority": buckets["low"], "by_type": by_type, "recently_changed": opportunities[:5], "confidence": _confidence_label(overall), "evidence_count": len(evidence_sources), "missing_evidence": sorted(missing_all), "recommendations_count": min(8, len(opportunities)), "warnings_count": 2, "health_summary": {"societies_reviewed": len(societies), "opportunity_count": len(opportunities), "overall_priority": overall}},
        "debug": debug_payload if include_debug else None,
    }
    return result
