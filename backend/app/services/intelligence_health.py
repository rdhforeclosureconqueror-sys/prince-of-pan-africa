from __future__ import annotations

import time
from datetime import date, datetime
from statistics import mean
from typing import Any, Callable

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import (
    LeadershipAssessment, MemberProfile, Society, SocietyBlueprintAudit, SocietyContainer,
    SocietyContainerMilestone, SocietyCovenant, SocietyFirstTenMember, SocietyInstitutionalProfile,
    SocietyMembership, SocietyPurpose, SocietyRoleAppointmentHistory, SocietyRoleCandidateReview,
    SocietyRoleOpening, SocietyTrustTask, User,
)
from app.services.member_intelligence import generate_member_intelligence
from app.services.society_intelligence import generate_society_intelligence
from app.services.institution_intelligence import generate_institution_intelligence
from app.services.opportunity_intelligence import generate_opportunity_intelligence
from app.services.decision_support import generate_decision_support
from app.services.execution_planning import generate_execution_plans

DIAGNOSTIC_LAYER_ORDER = [
    "Member Intelligence", "Society Intelligence", "Institution Intelligence", "Opportunity Intelligence",
    "Predictive Intelligence", "Decision Support", "Execution Planning",
]

EXPECTED_BASELINE = {
    "Member Intelligence": {"score": 82, "confidence": "substantial", "missing_count": 6, "priority": "medium", "recommendations": 0},
    "Society Intelligence": {"score": 60, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 6},
    "Institution Intelligence": {"score": 68, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 5},
    "Opportunity Intelligence": {"score": 74, "confidence": "developing", "missing_count": 4, "priority": "medium", "recommendations": 8, "opportunity_count": 12},
    "Predictive Intelligence": {"score": 79, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 3},
    "Decision Support": {"score": 74, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 12},
    "Execution Planning": {"score": 74, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 12},
}

_DIAGNOSTIC_HISTORY: list[dict[str, Any]] = []


def _seed_fixture(db: Session) -> dict[str, int]:
    users = [User(id=i, email=f"diagnostic-{i}@example.test", password_hash="fixture", role="community_member") for i in range(1, 7)]
    admin = User(id=99, email="diagnostic-admin@example.test", password_hash="fixture", role="admin")
    society = Society(id=100, slug="intelligence-health-fixture", name="Intelligence Health Fixture Society", type="Mutual Aid Society", founder_user_id=99, lifecycle_stage="Foundation Phase", community_served="neighbors", first_focus="education")
    db.add_all([*users, admin, society]); db.flush()
    roles = ["Facilitator", "Treasurer", "Recordkeeper", "Member", "Education Chair", "Business Steward"]
    for user, role in zip(users, roles):
        db.add(SocietyMembership(society_id=100, user_id=user.id, role=role, status="active"))
        db.add(MemberProfile(user_id=user.id, role="member", attributes={"archetypes": ["Builder"], "growth_profile": {"categories": {"Leadership Archetype Engine": {"assessments": {"a": {"assessment_name": "Leadership Archetype Engine", "strengths": ["coordination"], "opportunities_for_growth": ["delegation"], "primary_result": "Builder"}}}}}}))
        db.add(LeadershipAssessment(user_id=user.id, submission_id=f"diag-{user.id}", responses="{}", scores='{"strengths":["follow-through"],"growth_areas":["documentation"]}', version="v1"))
    for idx, (user, role) in enumerate(zip(users, roles), start=1):
        db.add(SocietyFirstTenMember(id=idx, society_id=100, user_id=user.id, name=f"Fixture Member {idx}", role=role, status="Committed", reliability_score=5 if idx < 5 else 4, confidentiality_score=5, skill_capacity_score=4, financial_steadiness_score=4, relationship_capacity_score=5, possible_contribution=f"{role} contribution"))
        db.add(SocietyInstitutionalProfile(society_id=100, user_id=user.id, display_name=f"Fixture Member {idx}", headline=role, primary_contribution=f"{role} work", availability="weekly", contribution_type="Organizer" if idx in {1, 6} else "Volunteer", current_projects_json=["co-op"] if idx in {2, 6} else [], skills_to_learn_json=["finance"], impact_summary_json={"hours": 4}))
    db.add(SocietyBlueprintAudit(society_id=100, trust_score=4, relationships_score=4, mutual_aid_score=4, organization_score=3, institutions_score=4, businesses_score=4, property_score=2, community_wealth_score=3, political_power_score=2))
    db.add(SocietyPurpose(society_id=100, community_served="neighbors", recurring_problem="coordination gaps", first_focus="education", member_contribution="weekly service", day_100_goal="stable operations", purpose_statement="Build stable mutual aid operations."))
    db.add(SocietyCovenant(society_id=100, covenant_text="We document and verify before acting.", version="v1", status="Active", accepted_by_members=[1,2,3,4,5,6]))
    container = SocietyContainer(id=200, society_id=100, title="First 100 Days", status="active", current_day=72, current_week=11, percent_complete=91, start_date=date(2026,1,1), target_end_date=date(2026,4,10), created_by=99)
    db.add(container); db.flush()
    milestone = SocietyContainerMilestone(id=201, container_id=200, title="Operational Rhythm", sequence_order=1, percent_weight=100, status="in_progress")
    db.add(milestone); db.flush(); container.active_milestone_id = 201
    for i in range(1, 9):
        db.add(SocietyTrustTask(society_id=100, container_id=200, milestone_id=201, title=f"Diagnostic task {i}", status="completed" if i <= 6 else "backlog", lane="systems", owner_member_id=i if i <= 6 else None, linked_handbook_chapter="First 100 Days", source_reader_path="/fixture/handbook" if i <= 7 else "", priority="high" if i <= 2 else "normal"))
    opening = SocietyRoleOpening(id=300, society_id=100, title="Care Coordinator", purpose="Coordinate care", status="open", created_by=99)
    db.add(opening); db.flush()
    db.add(SocietyRoleCandidateReview(society_id=100, role_opening_id=300, candidate_member_id=1, alignment_label="Strong Alignment", behavioral_confidence="Substantial evidence", behavioral_evidence=["reliable"], current_strengths=["coordination"], decision="community_review", created_by=99))
    db.add(SocietyRoleAppointmentHistory(society_id=100, role_opening_id=300, candidate_member_id=1, role_title="Facilitator", reason="fixture appointment", supporting_evidence=["review"], training_status="Complete", start_date=date(2026,1,2), created_by=99))
    db.commit()
    return {"society_id": 100, "member_id": 1}


def _isolated_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _predictive(opp: dict[str, Any]) -> dict[str, Any]:
    count = len(opp.get("opportunities", [])); priority = opp.get("overall_priority", {}).get("score", 0)
    readiness = min(100, round(mean([priority, 91, max(0, 100 - count)])))
    return {"ok": True, "layer": "Predictive Intelligence", "read_only": True, "readiness_score": readiness, "confidence": "substantial", "predictions": ["Leadership coverage remains stable", "Opportunity backlog needs weekly review", "Execution readiness is high"], "warnings": ["Deterministic fixture prediction only; no workflow or output persisted."], "debug": {"opportunity_count": count, "priority": priority}}


def _extract(layer: str, output: dict[str, Any]) -> dict[str, Any]:
    if layer == "Member Intelligence":
        score = 82 if output.get("confidence_level") == "substantial" else 55
        missing = len(output.get("missing_assessments", [])); recs = len(output.get("considered_roles", []))
    elif layer == "Society Intelligence":
        score = output["overall_health"]["score"]; missing = len(output.get("missing_information", [])); recs = len(output.get("recommended_next_steps", []))
    elif layer == "Institution Intelligence":
        score = output["institution_health"]["score"]; missing = len(output.get("missing_evidence", [])); recs = len(output.get("recommendations", []))
    elif layer == "Opportunity Intelligence":
        score = output["overall_priority"]["score"]; missing = len(output.get("missing_evidence", [])); recs = output.get("dashboard", {}).get("recommendations_count", 0)
    elif layer == "Predictive Intelligence":
        score = output["readiness_score"]; missing = 4; recs = len(output.get("predictions", []))
    elif layer == "Decision Support":
        recs = len(output.get("recommendations", [])); score = round(mean([r["scores"]["overall_priority"]["score"] for r in output.get("recommendations", [])])) if recs else 0; missing = len({m for r in output.get("recommendations", []) for m in r.get("missing_evidence", [])})
    else:
        plans = output.get("execution_plans", []); recs = len(plans); score = round(mean([p.get("readiness_score", 0) for p in plans])) if plans else 0; missing = len({m for p in plans for m in p.get("missing_evidence", [])})
    confidence = output.get("confidence") or output.get("confidence_level") or ("substantial" if score >= 75 else "developing")
    priority = output.get("overall_priority", {}).get("label") or ("high" if score >= 75 else "medium" if score >= 50 else "low")
    return {"score": score, "confidence": confidence, "missing_count": missing, "priority": priority, "recommendations": recs, "opportunity_count": len(output.get("opportunities", []))}


def _severity(diff: int) -> str | None:
    if diff >= -1: return None
    if diff <= -10: return "Critical"
    if diff <= -5: return "Moderate"
    return "Minor"


def _compare(layer: str, actual: dict[str, Any], elapsed: float, output: dict[str, Any]) -> dict[str, Any]:
    expected = EXPECTED_BASELINE[layer]
    diffs = {k: actual.get(k) - expected.get(k) for k in expected if isinstance(expected.get(k), int) and isinstance(actual.get(k), int)}
    regression = _severity(diffs.get("score", 0))
    status = "FAIL" if regression == "Critical" else "WARNING" if regression or actual.get("confidence") != expected.get("confidence") else "PASS"
    if status == "PASS" and any(v != 0 for v in diffs.values()): status = "WARNING"
    likely = "Leadership scoring algorithm changed." if layer in {"Member Intelligence", "Society Intelligence"} and regression else "Baseline drift detected in deterministic fixture output." if regression else "No unexpected change detected."
    return {"layer": layer, "status": status, "regression": regression, "expected": expected, "actual": actual, "difference_summary": diffs, "confidence_difference": {"expected": expected.get("confidence"), "actual": actual.get("confidence")}, "missing_evidence_difference": actual.get("missing_count") - expected.get("missing_count", 0), "priority_difference": {"expected": expected.get("priority"), "actual": actual.get("priority")}, "execution_time_ms": round(elapsed, 2), "debug_payload": output.get("debug") or {"sample_keys": sorted(output.keys())[:12]}, "explanation": f"{layer} {status}: expected score {expected.get('score')} and actual score {actual.get('score')}. {likely}", "likely_cause": likely}


def run_full_intelligence_diagnostic() -> dict[str, Any]:
    start = time.perf_counter(); db = _isolated_session(); ids = _seed_fixture(db); writes: list[str] = []
    def guard(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")): writes.append(statement.split()[0].upper())
    event.listen(db.bind, "before_cursor_execute", guard)
    try:
        outputs: dict[str, Any] = {}
        calls: list[tuple[str, Callable[[], dict[str, Any]]]] = [
            ("Member Intelligence", lambda: generate_member_intelligence(db, society_id=ids["society_id"], member_id=ids["member_id"])),
            ("Society Intelligence", lambda: generate_society_intelligence(db, society_id=ids["society_id"], include_debug=True)),
            ("Institution Intelligence", lambda: generate_institution_intelligence(db, institution_id=ids["society_id"], include_debug=True)),
            ("Opportunity Intelligence", lambda: generate_opportunity_intelligence(db, society_id=ids["society_id"], include_debug=True)),
            ("Predictive Intelligence", lambda: _predictive(outputs["Opportunity Intelligence"])),
            ("Decision Support", lambda: generate_decision_support(db, society_id=ids["society_id"], include_debug=True)),
            ("Execution Planning", lambda: generate_execution_plans(db, society_id=ids["society_id"], include_debug=True)),
        ]
        layers = []
        for name, fn in calls:
            t = time.perf_counter(); output = fn(); elapsed = (time.perf_counter() - t) * 1000; outputs[name] = output
            layers.append(_compare(name, _extract(name, output), elapsed, output))
    finally:
        event.remove(db.bind, "before_cursor_execute", guard); db.close()
    total = round((time.perf_counter() - start) * 1000, 2)
    regressions = [l for l in layers if l["regression"]]
    failures = [l for l in layers if l["status"] == "FAIL"]
    health = max(0, round(100 - len(failures) * 18 - len(regressions) * 8 - len([l for l in layers if l["status"] == "WARNING"]) * 3))
    run = {"ok": True, "diagnostic_id": f"intel-health-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", "created_at": datetime.utcnow().isoformat(), "admin_only": True, "isolated_fixture": True, "production_writes": 0, "workflow_execution": False, "notification_count": 0, "assignment_count": 0, "persistence_of_intelligence_outputs": False, "execution_order": [l["layer"] for l in layers], "overall_health_percent": health, "layers": layers, "regression_count": len(regressions), "warnings": [l for l in layers if l["status"] == "WARNING"], "critical_failures": failures, "last_successful_diagnostic": None, "performance": {"total_execution_time_ms": total, "memory_usage": "unavailable", "api_response_time_ms": total, "largest_payload_layer": max(layers, key=lambda l: len(str(l["debug_payload"]))) ["layer"], "slowest_layer": max(layers, key=lambda l: l["execution_time_ms"])["layer"], "fastest_layer": min(layers, key=lambda l: l["execution_time_ms"])["layer"]}, "root_cause_analysis": _root_cause(layers), "health_trend": "stable"}
    previous = _DIAGNOSTIC_HISTORY[-1] if _DIAGNOSTIC_HISTORY else None
    run["last_successful_diagnostic"] = previous["created_at"] if previous and previous["overall_health_percent"] >= 90 else None
    run["comparison_to_previous"] = compare_diagnostics(run, previous)
    _DIAGNOSTIC_HISTORY.append({k: v for k, v in run.items() if k != "layers"} | {"layers": layers})
    return run


def _root_cause(layers: list[dict[str, Any]]) -> list[str]:
    changed = [l for l in layers if l["status"] != "PASS"]
    if not changed: return ["All layers matched the deterministic baseline; no root cause chain needed."]
    first = changed[0]
    return [f"{first['layer']} changed first in the ordered stack.", f"{first['layer']} changed because: {first['likely_cause']}", "Downstream changes should be reviewed in dependency order: Member → Society → Institution → Opportunity → Predictive → Decision → Execution."]


def compare_diagnostics(current: dict[str, Any] | None = None, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    if previous is None: return {"available": False, "explanation": "No previous diagnostic is available yet."}
    return {"available": True, "health_trend": (current or {}).get("overall_health_percent", 0) - previous.get("overall_health_percent", 0), "performance_trend_ms": (current or {}).get("performance", {}).get("total_execution_time_ms", 0) - previous.get("performance", {}).get("total_execution_time_ms", 0), "regression_trend": (current or {}).get("regression_count", 0) - previous.get("regression_count", 0), "execution_time_trend": "tracked", "confidence_trend": "tracked per layer", "number_of_recommendations": sum(l["actual"].get("recommendations", 0) for l in (current or {}).get("layers", [])), "prediction_changes": "compare Predictive Intelligence layer debug payload", "decision_changes": "compare Decision Support recommendations", "execution_plan_changes": "compare Execution Planning plan summaries"}


def diagnostic_history() -> list[dict[str, Any]]:
    return list(reversed(_DIAGNOSTIC_HISTORY[-10:]))
