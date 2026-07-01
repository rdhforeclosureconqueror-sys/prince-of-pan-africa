from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.services.decision_support import generate_decision_support

READ_ONLY_WARNING = "These are recommendations only. No workflows, assignments, notifications, tasks, calendar events, Kanban cards, or database writes are performed. Human approval is required before execution."
PLAN_CATEGORIES = ["Quick Wins", "High Impact Projects", "Society Growth", "Leadership Development", "Institution Building", "Business Development", "Education", "Community Trust", "Volunteer Expansion", "Infrastructure", "Technology", "Resource Allocation", "Risk Reduction"]


def _effort_label(score: int) -> str:
    return "low" if score <= 35 else "medium" if score <= 65 else "high"


def _time_estimate(effort: int, priority: str) -> str:
    if effort <= 35:
        return "1–2 weeks"
    if effort <= 65:
        return "30–60 days" if priority in {"critical", "high"} else "60–90 days"
    return "90–180 days"


def _category(decision: dict[str, Any]) -> str:
    dtype = decision.get("decision_type")
    title = (decision.get("title") or "").lower()
    if decision.get("impact_score", 0) >= 60 and decision.get("effort_score", 100) <= 40:
        return "Quick Wins"
    if dtype == "leadership" or "role" in title:
        return "Leadership Development"
    if dtype == "institution":
        return "Institution Building"
    if dtype == "business":
        return "Business Development"
    if dtype == "resources":
        return "Resource Allocation"
    if dtype == "risks" or decision.get("urgency", 0) >= 80:
        return "Risk Reduction"
    if "trust" in title:
        return "Community Trust"
    if "education" in title or "training" in title:
        return "Education"
    if "container" in title:
        return "Infrastructure"
    if "volunteer" in title:
        return "Volunteer Expansion"
    if dtype == "society":
        return "Society Growth"
    return "High Impact Projects"


def _roles(decision: dict[str, Any]) -> list[str]:
    dtype = decision.get("decision_type")
    base = ["Human executive sponsor", "Society facilitator", "Recordkeeper"]
    if dtype == "business":
        base += ["Business lead", "Treasurer"]
    elif dtype == "institution":
        base += ["Institution steward", "Governance reviewer"]
    elif dtype == "leadership":
        base += ["Leadership mentor", "Training coordinator"]
    elif dtype == "resources":
        base += ["Resource coordinator", "Volunteer coordinator"]
    elif dtype == "risks":
        base += ["Risk reviewer", "Community trust steward"]
    return list(dict.fromkeys(base))


def _steps(decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"sequence": 1, "step": "Review the recommendation and confirm the objective with human leaders.", "human_approval_required": True},
        {"sequence": 2, "step": "Validate supporting evidence, missing evidence, assumptions, dependencies, and risks.", "human_approval_required": True},
        {"sequence": 3, "step": "Confirm required people, institutions, skills, resources, cost range, and timeline.", "human_approval_required": True},
        {"sequence": 4, "step": "Decide whether to approve, revise, defer, or reject the plan outside this read-only system.", "human_approval_required": True},
    ]


def _plan(decision: dict[str, Any]) -> dict[str, Any]:
    effort = int(decision.get("effort_score", 50))
    overall = int(decision.get("scores", {}).get("overall_priority", {}).get("score", decision.get("impact_score", 50)))
    related = decision.get("related_entities") or {}
    category = _category(decision)
    cost = "No direct cost estimated" if effort <= 35 else "$500–$2,500 planning range" if effort <= 65 else "$2,500+ planning range; requires budget review"
    return {
        "id": f"execution-plan-{decision['id']}",
        "source_recommendation_id": decision["id"],
        "category": category,
        "objective": decision.get("title"),
        "why_this_matters": decision.get("reasoning"),
        "expected_impact": decision.get("expected_outcomes", []),
        "priority": decision.get("priority"),
        "confidence": decision.get("confidence"),
        "estimated_effort": _effort_label(effort),
        "effort_score": effort,
        "time_estimate": _time_estimate(effort, decision.get("priority", "medium")),
        "required_roles": _roles(decision),
        "required_skills": ["Facilitation", "Evidence review", "Recordkeeping", "Community communication", "Risk assessment"],
        "required_members": related.get("members", []),
        "required_institutions": related.get("institutions", []),
        "required_containers": related.get("containers", []),
        "dependencies": decision.get("dependencies", []),
        "risks": decision.get("tradeoffs", []),
        "mitigation_suggestions": ["Hold manual leadership review before action.", "Resolve missing evidence before committing resources.", "Assign accountability only after separate approval."],
        "recommended_sequence_of_steps": _steps(decision),
        "milestones": ["Recommendation reviewed", "Evidence validated", "Resources confirmed", "Human approval decision recorded outside this system"],
        "success_metrics": ["Leader approval clarity", "Evidence gaps closed", "Required roles confirmed", "Community benefit remains explicit"],
        "required_resources": ["Leadership review time", "Relevant intelligence summaries", "Meeting notes template", "Budget estimate if approved"],
        "estimated_cost": cost,
        "estimated_community_benefit": decision.get("scores", {}).get("community_benefit", {}).get("score"),
        "estimated_institutional_benefit": decision.get("scores", {}).get("institution_benefit", {}).get("score"),
        "evidence_supporting_recommendation": decision.get("evidence", []),
        "missing_evidence": decision.get("missing_evidence", []),
        "assumptions": decision.get("assumptions", []),
        "manual_review_requirements": ["Human leaders must approve before any execution.", "No automated assignments or workflows are authorized by this plan."],
        "readiness_score": max(0, min(100, round(mean([overall, 100 - effort, 100 - min(70, len(decision.get("missing_evidence", [])) * 15)])))),
        "requires_manual_review": True,
        "no_execution_performed": True,
    }


def generate_execution_plans(db: Session, *, society_id: int | None = None, include_debug: bool = False) -> dict[str, Any]:
    ds = generate_decision_support(db, society_id=society_id, include_debug=include_debug)
    plans = [_plan(d) for d in ds.get("recommendations", [])]
    plans.sort(key=lambda p: (-p["readiness_score"], p["effort_score"], p["category"], p["id"]))
    grouped = {c: [p for p in plans if p["category"] == c] for c in PLAN_CATEGORIES}
    dashboard = {
        "executive_summary": {"total_plans": len(plans), "top_plan": plans[0]["objective"] if plans else "No execution plans", "read_only_boundary": READ_ONLY_WARNING},
        "recommended_plans": plans[:12],
        "quick_wins": grouped["Quick Wins"],
        "long_term_initiatives": [p for p in plans if p["estimated_effort"] == "high" or p["time_estimate"] == "90–180 days"],
        "timeline_view": {"1–2 weeks": [p for p in plans if p["time_estimate"] == "1–2 weeks"], "30–90 days": [p for p in plans if p["time_estimate"] in {"30–60 days", "60–90 days"}], "90–180 days": [p for p in plans if p["time_estimate"] == "90–180 days"]},
        "dependencies": sorted({d for p in plans for d in p["dependencies"]}),
        "required_people": sorted({r for p in plans for r in p["required_roles"]}),
        "required_resources": sorted({r for p in plans for r in p["required_resources"]}),
        "expected_outcomes": [o for p in plans for o in p["expected_impact"]][:20],
        "risks": sorted({r for p in plans for r in p["risks"]}),
        "success_metrics": sorted({m for p in plans for m in p["success_metrics"]}),
        "readiness_score": round(mean([p["readiness_score"] for p in plans])) if plans else 0,
    }
    return {"ok": True, "layer": "Execution Planning", "read_only": True, "warnings": [READ_ONLY_WARNING], "intelligence_inputs": ds.get("intelligence_inputs", []) + ["Decision Support"], "plan_categories": PLAN_CATEGORIES, "execution_plans": plans, "grouped_plans": grouped, "dashboard": dashboard, "debug": {"decision_support": ds} if include_debug else None}
