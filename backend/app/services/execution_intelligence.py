from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models import Society, SocietyBlueprintAudit, SocietyContainer, SocietyContainerMilestone, SocietyTrustTask
from app.services.execution_planning import generate_execution_plans

READ_ONLY_WARNING = "Read-only Execution Intelligence: compares plans against observed records only; no members, institutions, tasks, events, notifications, workflows, Kanban cards, roles, permissions, or financial records are created or changed."


def _pct(part: int, whole: int) -> int:
    return round((part / whole) * 100) if whole else 0


def _confidence(evidence: int, missing: int) -> str:
    score = max(0, min(100, evidence * 10 - missing * 8))
    return "high" if score >= 75 else "substantial" if score >= 55 else "developing" if score >= 30 else "limited"


def _days_between(start: date | None, end: date | None) -> int | None:
    if not start or not end:
        return None
    return max(0, (end - start).days)


def generate_execution_intelligence(db: Session, *, society_id: int | None = None, include_debug: bool = False) -> dict[str, Any]:
    query = db.query(Society)
    if society_id is not None:
        query = query.filter(Society.id == society_id)
    societies = query.order_by(Society.id).all()
    if society_id is not None and not societies:
        raise ValueError("Society not found")

    plans = generate_execution_plans(db, society_id=society_id, include_debug=include_debug)
    containers = db.query(SocietyContainer).filter(SocietyContainer.society_id.in_([s.id for s in societies])).all() if societies else []
    container_ids = [c.id for c in containers]
    tasks = db.query(SocietyTrustTask).filter(SocietyTrustTask.container_id.in_(container_ids)).all() if container_ids else []
    milestones = db.query(SocietyContainerMilestone).filter(SocietyContainerMilestone.container_id.in_(container_ids)).all() if container_ids else []
    audits = db.query(SocietyBlueprintAudit).filter(SocietyBlueprintAudit.society_id.in_([s.id for s in societies])).order_by(SocietyBlueprintAudit.created_at.asc()).all() if societies else []

    completed_tasks = [t for t in tasks if t.status == "completed"]
    blocked = [t for t in tasks if t.blocked_reason or t.status in {"blocked", "waiting"}]
    today = date.today()
    delayed = [t for t in tasks if t.due_date and t.due_date < today and t.status != "completed"]
    missed_milestones = [m for m in milestones if m.status not in {"completed", "done"}]
    completion_percentage = _pct(len(completed_tasks), len(tasks))
    planned_completion = round(mean([p.get("readiness_score", 0) for p in plans.get("execution_plans", [])])) if plans.get("execution_plans") else 0
    actual_completion = round(mean([completion_percentage, round(mean([c.percent_complete for c in containers])) if containers else 0])) if containers or tasks else 0
    latest_audit = audits[-1] if audits else None
    first_audit = audits[0] if audits else None
    measured_trust_change = ((latest_audit.trust_score - first_audit.trust_score) if latest_audit and first_audit else 0)
    expected_trust_change = 1 if plans.get("execution_plans") else 0
    expected_timeline_days = round(mean([d for d in [_days_between(c.start_date, c.target_end_date) for c in containers] if d is not None])) if containers else None
    actual_timeline_days = round(mean([max(c.current_day, 0) for c in containers])) if containers else None
    evidence = [f"{len(plans.get('execution_plans', []))} read-only execution plans", f"{len(tasks)} Trust Board tasks", f"{len(completed_tasks)} completed tasks", f"{len(containers)} containers", f"{len(audits)} blueprint audits"]
    missing = []
    if not tasks: missing.append("Task completion evidence")
    if not audits: missing.append("Before/after trust audit evidence")
    if not containers: missing.append("Execution container records")
    if not any(t.completed_at for t in tasks): missing.append("Task completion timestamps")

    variances = {
        "planned_completion_vs_actual_completion": actual_completion - planned_completion,
        "planned_participation_vs_actual_participation": len({p for plan in plans.get("execution_plans", []) for p in plan.get("required_members", [])}) - len({t.owner_member_id for t in tasks if t.owner_member_id}),
        "expected_trust_change_vs_measured_trust_change": measured_trust_change - expected_trust_change,
        "expected_leadership_growth_vs_actual_growth": len([p for p in plans.get("execution_plans", []) if p.get("category") == "Leadership Development"]) - len([m for m in milestones if "lead" in m.title.lower()]),
        "expected_business_outcomes_vs_actual_outcomes": len([p for p in plans.get("execution_plans", []) if p.get("category") == "Business Development"]) - len([t for t in tasks if "business" in (t.title + t.description).lower()]),
        "expected_timelines_vs_actual_timelines": (actual_timeline_days - expected_timeline_days) if actual_timeline_days is not None and expected_timeline_days is not None else None,
        "expected_resources_vs_actual_resources": len(plans.get("dashboard", {}).get("required_resources", [])) - len({t.linked_module for t in tasks if t.linked_module}),
        "expected_risks_vs_realized_risks": len(plans.get("dashboard", {}).get("risks", [])) - len(blocked),
    }
    score = max(0, min(100, round(mean([actual_completion, completion_percentage, max(0, 100 - len(blocked) * 8), max(0, 100 - len(delayed) * 10)]))))
    return {"ok": True, "layer": "Execution Intelligence", "version": "v1", "read_only": True, "warnings": [READ_ONLY_WARNING], "execution_score": score, "success_score": round(mean([score, max(0, 100 + min(0, variances['planned_completion_vs_actual_completion']))])), "completion_percentage": completion_percentage, "variance_analysis": variances, "bottlenecks": [t.title for t in blocked[:8]], "delays": [t.title for t in delayed[:8]], "missed_milestones": [m.title for m in missed_milestones[:8]], "over_performing_areas": [k for k, v in variances.items() if isinstance(v, int) and v > 0], "under_performing_areas": [k for k, v in variances.items() if isinstance(v, int) and v < 0], "confidence": _confidence(len(evidence), len(missing)), "evidence": evidence, "missing_evidence": missing, "assumptions": ["Execution plans are read-only expected state.", "Trust Board tasks and containers are treated as actual execution evidence."], "recommended_lessons_learned": ["Record completion timestamps on execution tasks.", "Capture before/after trust audits for each major plan.", "Review blocked and delayed items before approving new work."], "debug": {"execution_planning": plans} if include_debug else None}
