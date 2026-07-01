from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.services.opportunity_intelligence import generate_opportunity_intelligence

READ_ONLY_WARNING = "Read-only generated Decision Support: no records are written, no workflows are executed, no tasks are created, no members are assigned, no notifications are sent, no calendar events or Kanban cards are created, and human leaders make every final decision."
DECISION_TYPES = ["leadership", "society", "institution", "members", "containers", "business", "resources", "risks"]


def _label(score: int) -> str:
    return "critical" if score >= 85 else "high" if score >= 70 else "medium" if score >= 45 else "low"


def _confidence(score: int, evidence: list[str], missing: list[str]) -> str:
    value = round(mean([score, min(100, len(evidence) * 16), 100 - min(80, len(missing) * 12)]))
    return "substantial" if value >= 75 else "developing" if value >= 45 else "limited"


def _score(name: str, value: int, why: str) -> dict[str, Any]:
    return {"score": max(0, min(100, round(value))), "why": why}


def _decision(*, did: str, title: str, decision_type: str, source: dict[str, Any], impact: int, urgency: int, effort: int, risk_reduction: int, community_benefit: int, institution_benefit: int, long_term_value: int, evidence: list[str], missing: list[str] | None = None, assumptions: list[str] | None = None, tradeoffs: list[str] | None = None, dependencies: list[str] | None = None, outcomes: list[str] | None = None, related: dict[str, list[Any]] | None = None) -> dict[str, Any]:
    missing = missing or []
    parts = {
        "impact": impact,
        "urgency": urgency,
        "confidence": 80 if evidence and not missing else 55 if evidence else 30,
        "effort_inverse": 100 - effort,
        "risk_reduction": risk_reduction,
        "community_benefit": community_benefit,
        "institution_benefit": institution_benefit,
        "long_term_value": long_term_value,
    }
    overall = round(mean(parts.values()))
    score_explanations = {
        "impact": _score("Impact", impact, f"Impact is {impact} because the source recommendation priority/health signal is {source.get('priority_score', source.get('score', impact))} and affects {decision_type} planning."),
        "urgency": _score("Urgency", urgency, f"Urgency is {urgency} because lower readiness, blockers, missing roles, or risk indicators increase near-term attention."),
        "confidence": _score("Confidence", parts["confidence"], f"Confidence uses evidence count {len(evidence)} and missing evidence count {len(missing)}; missing evidence lowers the score."),
        "effort": _score("Effort", effort, f"Effort is {effort}; lower effort raises quick-win priority but does not replace human review."),
        "risk_reduction": _score("Risk Reduction", risk_reduction, f"Risk reduction is {risk_reduction} based on whether the decision addresses trust, role, workflow, operational, or strategic fragility."),
        "community_benefit": _score("Community Benefit", community_benefit, f"Community benefit is {community_benefit} based on likely member, volunteer, trust, education, or recognition value."),
        "institution_benefit": _score("Institution Benefit", institution_benefit, f"Institution benefit is {institution_benefit} based on governance, readiness, business, or container improvement potential."),
        "long_term_value": _score("Long-Term Value", long_term_value, f"Long-term value is {long_term_value} based on durable capacity, succession, education, and expansion value."),
        "overall_priority": _score("Overall Priority", overall, "Mean of impact, urgency, confidence, inverse effort, risk reduction, community benefit, institution benefit, and long-term value. No hidden or random ordering."),
    }
    return {
        "id": did,
        "title": title,
        "decision_type": decision_type,
        "priority": _label(overall),
        "impact_score": impact,
        "effort_score": effort,
        "urgency": urgency,
        "confidence": _confidence(parts["confidence"], evidence, missing),
        "evidence": evidence,
        "missing_evidence": missing,
        "assumptions": assumptions or ["All intelligence inputs are read-only generated outputs.", "Human leaders will validate context before choosing any action."],
        "reasoning": f"This recommendation exists to help leaders decide whether to focus on {title}. It prioritizes attention only and does not make or execute a decision.",
        "expected_outcomes": outcomes or ["Clearer human planning conversation.", "Improved prioritization after leaders review evidence."],
        "tradeoffs": tradeoffs or ["Focusing here may delay lower-priority opportunities.", "Acting with limited evidence may require additional manual validation first."],
        "dependencies": dependencies or ["Manual leadership review", "Updated intelligence evidence after any human action"],
        "related_entities": related or {},
        "requires_manual_review": True,
        "no_workflow_executed": True,
        "human_final_decision": "Required: human leaders make the final decision.",
        "scores": score_explanations,
    }


def _from_opportunity(o: dict[str, Any]) -> dict[str, Any]:
    typemap = {"role": "leadership", "leadership": "leadership", "assessment": "members", "volunteer": "resources", "mentorship": "resources", "business": "business", "institution": "institution", "society_growth": "society", "trust": "risks", "education": "resources", "recognition": "members"}
    dtype = typemap.get(o.get("type"), "society")
    effort = int(o.get("effort", 50))
    priority = int(o.get("priority_score", 50))
    impact = int(o.get("impact", priority))
    urgency = max(20, min(100, round(mean([priority, 100 - int(o.get("confidence", 50)) if isinstance(o.get("confidence"), int) else priority]))))
    return _decision(
        did=f"decision-{o['id']}", title=o["title"], decision_type=dtype, source=o,
        impact=impact, urgency=urgency, effort=effort,
        risk_reduction=85 if dtype == "risks" or o.get("type") in {"role", "leadership", "trust"} else 55,
        community_benefit=80 if dtype in {"members", "resources", "society", "leadership"} else 60,
        institution_benefit=85 if dtype in {"institution", "business", "containers", "leadership"} else 55,
        long_term_value=85 if dtype in {"institution", "leadership", "society", "business"} else 65,
        evidence=o.get("evidence", []), missing=o.get("missing_evidence", []),
        assumptions=["Recommendation is derived from Opportunity Intelligence, which reuses lower intelligence layers.", "No new persistence or task workflow is created."],
        tradeoffs=[f"Prioritizing {o['title']} may defer other {dtype} recommendations.", "Human review is required before any operational action."],
        dependencies=["Existing intelligence evidence", "Manual leader discussion"],
        outcomes=[o.get("recommended_action", "Manual review outcome"), "Better strategic focus without automated execution."],
        related={"members": o.get("related_members", []), "roles": o.get("related_roles", []), "containers": o.get("related_containers", []), "societies": o.get("related_societies", []), "institutions": o.get("related_institutions", [])},
    )


def generate_decision_support(db: Session, *, society_id: int | None = None, include_debug: bool = False) -> dict[str, Any]:
    opp = generate_opportunity_intelligence(db, society_id=society_id, include_debug=include_debug)
    decisions = [_from_opportunity(o) for o in opp.get("opportunities", [])]
    decisions.sort(key=lambda d: (-d["scores"]["overall_priority"]["score"], d["effort_score"], d["decision_type"], d["id"]))
    by_type = {t: [d for d in decisions if d["decision_type"] == t] for t in DECISION_TYPES}
    dashboard = {
        "executive_summary": {"total_recommendations": len(decisions), "top_priority": decisions[0]["title"] if decisions else "No current recommendations", "read_only_boundary": READ_ONLY_WARNING},
        "top_10_priorities": decisions[:10],
        "quick_wins": [d for d in decisions if d["impact_score"] >= 60 and d["effort_score"] <= 40][:10],
        "high_impact_low_effort": [d for d in decisions if d["impact_score"] >= 75 and d["effort_score"] <= 45],
        "high_impact_high_effort": [d for d in decisions if d["impact_score"] >= 75 and d["effort_score"] > 45],
        "critical_risks": [d for d in decisions if d["decision_type"] == "risks" or d["urgency"] >= 80][:10],
        "leadership_decisions": by_type["leadership"], "institution_decisions": by_type["institution"], "container_decisions": by_type["containers"] + [d for d in decisions if "container" in d["title"].lower()], "business_decisions": by_type["business"], "resource_allocation": by_type["resources"],
        "strategic_roadmap": decisions[:15],
    }
    return {"ok": True, "layer": "Decision Support", "read_only": True, "warnings": [READ_ONLY_WARNING, "Prioritizes decisions only; human leaders make final decisions."], "intelligence_inputs": ["Member Intelligence", "Society Intelligence", "Institution Intelligence", "Opportunity Intelligence", "Predictive Intelligence (if present in existing outputs)"], "recommendations": decisions, "dashboard": dashboard, "debug": {"opportunity_intelligence": opp} if include_debug else None}
