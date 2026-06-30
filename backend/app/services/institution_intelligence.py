from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.services.society_intelligence import generate_society_intelligence

SUPPORTED_INSTITUTION_TYPES = [
    "Mutual Aid Society", "Business", "Cooperative", "Learning Circle", "School",
    "Community Project", "Committee", "Health Circle", "Book Club", "Working Group",
]


def _score_alias(source: dict[str, Any], name: str, calculation_prefix: str = "") -> dict[str, Any]:
    score = dict(source)
    score["name"] = name
    if calculation_prefix:
        score["calculation"] = f"{calculation_prefix} {score.get('calculation', '')}".strip()
    return score


def _composite(name: str, parts: list[dict[str, Any]], explanation: str) -> dict[str, Any]:
    present = [p for p in parts if p]
    value = round(mean([p["score"] for p in present])) if present else 0
    evidence = [f"{p['name']}={p['score']} because {p['why']}" for p in present]
    missing = sorted({m for p in present for m in p.get("missing_evidence", [])})
    limited = sum(1 for p in present if p.get("confidence") == "limited")
    confidence = "limited" if not present or limited >= max(1, len(present) // 2) else "developing" if any(p.get("confidence") == "developing" for p in present) else "substantial"
    return {"name": name, "score": value, "why": "; ".join(evidence) if evidence else "No usable evidence found.", "evidence": evidence, "calculation": explanation, "confidence": confidence, "missing_evidence": missing}


def _recommendations(scores: dict[str, Any], missing_roles: list[str]) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    mapping = [
        ("leadership_health", "Fill missing leadership", "Leadership Health is below target or missing critical roles."),
        ("assessment_coverage", "Complete assessments", "Assessment Coverage is below target, so confidence in member-role fit is lower."),
        ("participation_health", "Increase participation", "Participation Health needs more active member, meeting, profile, or Trust Board participation evidence."),
        ("trust_health", "Improve trust", "Trust Health needs stronger Blueprint, First Ten, Mutual Aid, or Trust Board evidence."),
        ("container_completion", "Complete First 100 Days", "Container Completion shows unfinished existing container progress."),
        ("business_readiness", "Launch business", "Business Readiness evidence is not yet strong enough for business launch confidence."),
        ("operational_readiness", "Strengthen governance", "Operational Readiness depends on roles, purpose/covenant, knowledge, and container execution."),
    ]
    for key, action, why in mapping:
        if scores[key]["score"] < 70:
            recs.append({"action": action, "why": f"{why} Current score is {scores[key]['score']} because {scores[key]['why']} Recommendation only; no action is executed."})
    for role in missing_roles[:3]:
        recs.append({"action": f"Recruit members for {role}", "why": f"Role Coverage lists {role} as missing. Recommendation only; no role opening, workflow, or appointment is created."})
    return recs[:8] or [{"action": "Keep strengthening documented practice", "why": "Evidence shows no urgent gap above threshold; continue improving assessments, roles, participation, trust, and governance."}]


def generate_institution_intelligence(db: Session, *, institution_id: int, include_debug: bool = False) -> dict[str, Any]:
    society = generate_society_intelligence(db, society_id=institution_id, include_debug=include_debug)
    s = society["scores"]
    scores = {
        "trust_health": _score_alias(s["trust_score"], "Trust Health", "Reuses Society Intelligence Trust Score; no duplicate calculation."),
        "participation_health": _score_alias(s["participation_score"], "Participation Health", "Reuses Society Intelligence Participation Score; no duplicate calculation."),
        "leadership_health": _composite("Leadership Health", [s["leadership_coverage"], s["role_coverage"]], "Mean of Society Intelligence leadership coverage and role coverage; no duplicate role math."),
        "knowledge_health": _score_alias(s["knowledge_coverage"], "Knowledge Health", "Reuses Society Intelligence Knowledge Coverage; no duplicate calculation."),
        "financial_readiness": _composite("Financial Readiness", [s["business_readiness"], s["volunteer_capacity"]], "Mean of existing Business Readiness and Volunteer Capacity evidence as a financial readiness proxy."),
        "operational_readiness": _composite("Operational Readiness", [s["institution_readiness"], s["role_coverage"], s["knowledge_coverage"], s["first_100_days_progress"]], "Mean of existing institution readiness, role coverage, knowledge coverage, and container progress."),
        "business_readiness": _score_alias(s["business_readiness"], "Business Readiness", "Reuses Society Intelligence Business Readiness; no duplicate calculation."),
        "volunteer_capacity": _score_alias(s["volunteer_capacity"], "Volunteer Capacity", "Reuses Society Intelligence Volunteer Capacity; no duplicate calculation."),
        "role_coverage": _score_alias(s["role_coverage"], "Role Coverage", "Reuses Society Intelligence Role Coverage; no duplicate calculation."),
        "assessment_coverage": _score_alias(s["assessment_completion"], "Assessment Coverage", "Reuses Society Intelligence Assessment Completion; no duplicate calculation."),
        "container_completion": _score_alias(s["first_100_days_progress"], "Container Completion", "Uses existing SocietyContainer.percent_complete only; no workflow is activated."),
    }
    core = [scores[k] for k in ["leadership_health", "participation_health", "trust_health", "knowledge_health", "financial_readiness", "operational_readiness", "business_readiness", "volunteer_capacity", "role_coverage", "assessment_coverage", "container_completion"]]
    scores["institution_health"] = _composite("Institution Health", core, "Mean of explained Institution Intelligence domains, each derived from Society Intelligence and Member Intelligence evidence.")
    risk_level = "high" if scores["institution_health"]["score"] < 45 else "moderate" if scores["institution_health"]["score"] < 70 else "low"
    growth_potential = _composite("Growth Potential", [s["member_growth"], scores["business_readiness"], scores["operational_readiness"]], "Mean of member growth, business readiness, and operational readiness from existing evidence.")
    missing = sorted({m for score in scores.values() for m in score.get("missing_evidence", [])})
    result = {
        "ok": True,
        "institution_id": institution_id,
        "institution_name": society["society_name"],
        "institution_type": society.get("society_type") or "Future-compatible institution",
        "supported_institution_types": SUPPORTED_INSTITUTION_TYPES,
        "intelligence_hierarchy": ["Member Intelligence", "Society Intelligence", "Institution Intelligence"],
        "scores": scores,
        "institution_health": scores["institution_health"],
        "health_trend": {"label": "live_read_model", "why": "No historical Institution Intelligence is stored; trend reflects current generated evidence only."},
        "risk_level": {"level": risk_level, "why": f"Risk is {risk_level} because Institution Health is {scores['institution_health']['score']}."},
        "growth_potential": growth_potential,
        "institution_strengths": [x.replace("Society", "Institution") for x in society["top_strengths"]],
        "institution_weaknesses": society["top_risks"],
        "recommended_next_actions": _recommendations(scores, society["missing_roles"]),
        "warnings": ["Read-only generated model: it does not write records, execute workflows, create scheduled jobs, or begin Adaptive Kanban."] + society["warnings"],
        "confidence": society["confidence"],
        "evidence": society["evidence_sources"],
        "missing_evidence": missing,
        "calculation_explanation": "Institution Intelligence is a read-only aggregation layer. It reuses Society Intelligence and Member Intelligence outputs and existing role, participation, STAR, Mutual Aid, Trust Board, Blueprint, purpose/covenant, Knowledge Commons, project, container, Business Builder, leadership, meeting, and completion evidence where present.",
        "source_of_truth_boundary": "Member Intelligence remains source of truth for individuals. Society Intelligence remains source of truth for societies. Institution Intelligence is the source of truth for institution-level read models.",
        "debug": None,
    }
    if include_debug:
        result["debug"] = {"raw_institution_intelligence_json": {k: v for k, v in result.items() if k != "debug"}, "raw_society_intelligence_json": society, "calculations": scores, "confidence": society["confidence"], "fallback_reasons": society.get("debug", {}).get("fallback_reasons", []), "missing_evidence": missing, "read_only_boundary": result["warnings"][0]}
    return result
