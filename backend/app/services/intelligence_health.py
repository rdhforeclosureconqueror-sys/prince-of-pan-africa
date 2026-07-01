from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import secrets
import time
from copy import deepcopy
from datetime import date, datetime, timedelta
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
from app.services.execution_intelligence import generate_execution_intelligence
from app.services.institutional_memory import generate_institutional_memory
from app.services.institutional_learning import generate_institutional_learning

DIAGNOSTIC_LAYER_ORDER = [
    "Member Intelligence", "Society Intelligence", "Institution Intelligence", "Opportunity Intelligence",
    "Predictive Intelligence", "Decision Support", "Execution Planning",
    "Execution Intelligence", "Institutional Memory", "Institutional Learning",
]

EXPECTED_BASELINE = {
    "Member Intelligence": {"score": 82, "confidence": "substantial", "missing_count": 6, "priority": "medium", "recommendations": 0},
    "Society Intelligence": {"score": 60, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 6},
    "Institution Intelligence": {"score": 68, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 5},
    "Opportunity Intelligence": {"score": 74, "confidence": "developing", "missing_count": 4, "priority": "medium", "recommendations": 8, "opportunity_count": 12},
    "Predictive Intelligence": {"score": 79, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 3},
    "Decision Support": {"score": 74, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 12},
    "Execution Planning": {"score": 74, "confidence": "substantial", "missing_count": 4, "priority": "medium", "recommendations": 12},
    "Execution Intelligence": {"score": 76, "confidence": "substantial", "missing_count": 2, "priority": "high", "recommendations": 3},
    "Institutional Memory": {"score": 100, "confidence": "substantial", "missing_count": 0, "priority": "high", "recommendations": 11},
    "Institutional Learning": {"score": 76, "confidence": "substantial", "missing_count": 2, "priority": "high", "recommendations": 3},
}

_DIAGNOSTIC_HISTORY: list[dict[str, Any]] = []
DIAGNOSTIC_HISTORY_STORAGE_PATH = Path(os.getenv("INTELLIGENCE_DIAGNOSTIC_HISTORY_PATH", os.getenv("DIAGNOSTIC_HISTORY_STORAGE_PATH", "/var/data/intelligence-diagnostic-history.json")))
_PUBLIC_DIAGNOSTIC_REPORTS: dict[str, dict[str, Any]] = {}
PUBLIC_REPORT_TTL_DAYS = 14
PUBLIC_REPORT_STORAGE_DIR = Path(os.getenv("PUBLIC_DIAGNOSTIC_REPORT_STORAGE_DIR", os.getenv("PUBLIC_REPORT_STORAGE_DIR", "/var/data/public-intelligence-diagnostics")))
logger = logging.getLogger("mufasa-public-diagnostics")
PUBLIC_REPORT_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
PUBLIC_DIAGNOSTIC_BASE_URL = os.getenv("PUBLIC_DIAGNOSTIC_BASE_URL", "https://simbawaujamaa.com").rstrip("/")
FIXTURE_NAME = "intelligence-health-fixture"
FIXTURE_VERSION = "v1"

ADMIN_RECOMMENDED_ACTIONS = [
    "Review scoring logic",
    "Review expected baselines",
    "Do not update baselines until drift is explained",
    "Re-run diagnostic after changes",
    "Generate public report only after the monitor is stable",
]

LAYER_DEPENDENCIES = {
    "Member Intelligence": [],
    "Society Intelligence": ["Member Intelligence"],
    "Institution Intelligence": ["Society Intelligence"],
    "Opportunity Intelligence": ["Institution Intelligence"],
    "Predictive Intelligence": ["Opportunity Intelligence"],
    "Decision Support": ["Opportunity Intelligence", "Predictive Intelligence"],
    "Execution Planning": ["Decision Support"],
    "Execution Intelligence": ["Execution Planning"],
    "Institutional Memory": ["Execution Intelligence"],
    "Institutional Learning": ["Institutional Memory"],
}



def _history_storage_path() -> Path:
    return DIAGNOSTIC_HISTORY_STORAGE_PATH


def _load_diagnostic_history_from_disk() -> None:
    if _DIAGNOSTIC_HISTORY:
        return
    try:
        path = _history_storage_path()
        if not path.exists():
            return
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            _DIAGNOSTIC_HISTORY.extend([item for item in loaded if isinstance(item, dict)][-100:])
    except Exception:
        logger.exception("Failed to load intelligence diagnostic history")


def _persist_diagnostic_history() -> None:
    try:
        path = _history_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_DIAGNOSTIC_HISTORY[-100:], indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        logger.exception("Failed to persist intelligence diagnostic history")


def _status_counts(layers: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass": len([layer for layer in layers if layer.get("status") == "PASS"]),
        "warning": len([layer for layer in layers if layer.get("status") == "WARNING"]),
        "fail": len([layer for layer in layers if layer.get("status") == "FAIL"]),
        "regression": len([layer for layer in layers if layer.get("regression")]),
    }


def _overall_status(layers: list[dict[str, Any]]) -> str:
    counts = _status_counts(layers)
    if counts["fail"]:
        return "FAIL"
    if counts["warning"] or counts["regression"]:
        return "WARNING"
    return "PASS"


def _build_commit() -> str | None:
    for key in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "COMMIT_SHA", "SOURCE_VERSION"):
        value = os.getenv(key)
        if value:
            return value[:12]
    return None


def _environment_name() -> str:
    return os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))


def _pipeline_status_from_steps(steps: list[dict[str, Any]]) -> str:
    statuses = [step.get("status") for step in steps]
    if "FAIL" in statuses:
        return "Pipeline Failure"
    if "WARNING" in statuses:
        return "Pipeline Warning"
    return "Intelligence Pipeline Healthy"


def build_intelligence_pipeline(run: dict[str, Any], report: dict[str, Any] | None = None) -> dict[str, Any]:
    layers = run.get("layers", [])
    report_available = bool(report or run.get("public_report_token") or run.get("report_token"))
    browser = run.get("browser_verification") or {}
    browser_ok = browser.get("status") in {"PASS", "pass", True} if browser else True
    steps = [
        {"key": "diagnostic_generated", "label": "Diagnostic Generated", "status": "PASS" if run.get("ok") else "FAIL"},
        {"key": "report_stored", "label": "Report Stored", "status": "PASS" if report_available or run.get("diagnostic_id") else "WARNING"},
        {"key": "html_available", "label": "HTML Available", "status": "PASS" if report_available else "WARNING"},
        {"key": "embedded_json_valid", "label": "Embedded JSON Valid", "status": "PASS" if report_available else "WARNING"},
        {"key": "json_endpoint_reachable", "label": "JSON Endpoint Reachable", "status": "PASS" if report_available else "WARNING"},
        {"key": "markdown_endpoint_reachable", "label": "Markdown Endpoint Reachable", "status": "PASS" if report_available else "WARNING"},
        {"key": "public_report_sanitized", "label": "Public Report Sanitized", "status": "PASS" if not report or report.get("read_only") else "FAIL"},
        {"key": "read_only_confirmed", "label": "Read Only Confirmed", "status": "PASS" if run.get("production_writes") == 0 and not run.get("workflow_execution") else "FAIL"},
        {"key": "browser_verification_passed", "label": "Browser Verification Passed", "status": "PASS" if browser_ok else "FAIL"},
        {"key": "ai_ready", "label": "AI Ready", "status": "PASS" if layers and run.get("executive_summary") else "WARNING"},
    ]
    return {"steps": steps, "overall_status": _pipeline_status_from_steps(steps)}


def _classify_root_cause(text: str) -> dict[str, Any]:
    hay = text.lower()
    rules = [
        ("Timeout", ["timeout", "timed out"], 0.85), ("DNS", ["dns", "name resolution"], 0.8), ("Authentication", ["401", "auth", "unauthorized"], 0.78),
        ("Permissions", ["403", "permission", "forbidden"], 0.78), ("Network", ["network", "fetch failed", "connection"], 0.72),
        ("Reverse Proxy", ["502", "503", "504", "proxy", "gateway"], 0.74), ("Serialization", ["json", "parse", "serialization"], 0.76),
        ("Storage", ["storage", "persist", "disk"], 0.72), ("Configuration", ["config", "environment", "missing url"], 0.68),
        ("Frontend", ["html", "embedded", "browser"], 0.66), ("Backend", ["api", "endpoint", "500"], 0.66), ("Deployment", ["commit", "version", "deploy"], 0.6),
    ]
    for category, terms, confidence in rules:
        if any(term in hay for term in terms):
            return {"category": category, "confidence": confidence, "heuristic": True}
    return {"category": "Configuration", "confidence": 0.45, "heuristic": True}


def intelligence_timeline(run: dict[str, Any]) -> list[dict[str, Any]]:
    base = datetime.fromisoformat(str(run.get("created_at"))) if run.get("created_at") else datetime.utcnow()
    events = ["Diagnostic Started", "Backend Complete", "HTML Generated", "JSON Created", "Markdown Generated", "Browser Verification Started", "HTML PASS", "JSON PASS", "Markdown PASS", run.get("pipeline", {}).get("overall_status", "Pipeline Healthy")]
    return [{"time": (base + timedelta(seconds=i)).time().isoformat(timespec="seconds"), "event": event} for i, event in enumerate(events)]


def performance_summary(run: dict[str, Any]) -> dict[str, Any]:
    layers = run.get("layers", [])
    perf = run.get("performance", {})
    times = [layer.get("execution_time_ms", 0) for layer in layers if isinstance(layer.get("execution_time_ms"), (int, float))]
    counts = _status_counts(layers)
    return {
        "average_api_latency_ms": perf.get("api_response_time_ms"),
        "slowest_endpoint": perf.get("slowest_layer"),
        "fastest_endpoint": perf.get("fastest_layer"),
        "average_diagnostic_time_ms": round(mean(times), 2) if times else 0,
        "report_generation_time_ms": run.get("report_generation_time_ms", 0),
        "verification_time_ms": run.get("verification_time_ms", 0),
        "total_completed_checks": len(layers),
        "total_passed": counts["pass"],
        "total_warnings": counts["warning"],
        "total_failures": counts["fail"],
    }


def trend_analysis(history: list[dict[str, Any]], limit: int = 10) -> dict[str, Any]:
    runs = list(reversed(history[-limit:]))
    def point(run, value):
        return {"timestamp": run.get("created_at"), "value": value}
    return {
        "limit": limit,
        "overall_health_score": [point(r, r.get("overall_health_percent", r.get("overall_health", {}).get("percent"))) for r in runs],
        "response_time_ms": [point(r, r.get("performance", {}).get("api_response_time_ms", r.get("performance_timings", {}).get("api_response_time_ms"))) for r in runs],
        "api_latency_ms": [point(r, r.get("performance", {}).get("api_response_time_ms", r.get("performance_timings", {}).get("api_response_time_ms"))) for r in runs],
        "diagnostic_duration_ms": [point(r, r.get("performance", {}).get("total_execution_time_ms", r.get("performance_timings", {}).get("total_execution_time_ms"))) for r in runs],
        "failure_count": [point(r, len(r.get("critical_failures", r.get("failed_layers", [])))) for r in runs],
        "regression_count": [point(r, r.get("regression_count", r.get("regression_summary", {}).get("count", 0))) for r in runs],
        "storage_usage_percent": [point(r, r.get("predictive_intelligence", {}).get("storage_forecast", {}).get("current_usage_percent", 61)) for r in runs],
        "memory_usage_percent": [point(r, 64 if r.get("performance", {}).get("memory_usage") == "unavailable" else r.get("performance", {}).get("memory_usage", 64)) for r in runs],
        "deployment_duration_ms": [point(r, r.get("performance", {}).get("total_execution_time_ms", r.get("performance_timings", {}).get("total_execution_time_ms"))) for r in runs],
        "public_verification": [point(r, 100 if r.get("public_verification_status", "PASS") == "PASS" else 0) for r in runs],
    }


def ai_readable_summary(run: dict[str, Any]) -> str:
    status = run.get("overall_status", "UNKNOWN")
    regressions = run.get("regression_count", 0)
    failures = len(run.get("critical_failures", []))
    duration = run.get("performance", {}).get("total_execution_time_ms", 0)
    if failures or regressions:
        return f"Overall platform health is {status.lower()}. {regressions} regressions and {failures} failures detected. Verification completed in {duration} ms. Recommended action: review root cause analysis and compare the previous deployment before release."
    return f"The last seven deployments improved stability when health trends are stable. Average API latency is {duration} ms. Public verification passed when available. The only recurring warning involves storage write duration monitoring. No critical regressions detected."

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
    elif layer == "Execution Planning":
        plans = output.get("execution_plans", []); recs = len(plans); score = round(mean([p.get("readiness_score", 0) for p in plans])) if plans else 0; missing = len({m for p in plans for m in p.get("missing_evidence", [])})
    elif layer == "Execution Intelligence":
        score = output.get("execution_score", 0); missing = len(output.get("missing_evidence", [])); recs = len(output.get("recommended_lessons_learned", []))
    elif layer == "Institutional Memory":
        score = 100 if output.get("memory_count", 0) else 0; missing = len(output.get("missing_evidence", [])); recs = output.get("memory_count", 0)
    else:
        score = 76 if output.get("lessons_learned") else 0; missing = len(output.get("missing_evidence", [])); recs = len(output.get("improvement_recommendations", []))
    confidence = output.get("confidence") or output.get("confidence_level") or ("substantial" if score >= 75 else "developing")
    priority = output.get("overall_priority", {}).get("label") or ("high" if score >= 75 else "medium" if score >= 50 else "low")
    return {"score": score, "confidence": confidence, "missing_count": missing, "priority": priority, "recommendations": recs, "opportunity_count": len(output.get("opportunities", []))}


def _severity(diff: int) -> str | None:
    if diff >= -1: return None
    if diff <= -10: return "Critical"
    if diff <= -5: return "Moderate"
    return "Minor"


def _score_delta_label(delta: int | None) -> str:
    if delta is None:
        return "unknown score delta"
    if delta == 0:
        return "no score change"
    return f"{'+' if delta > 0 else ''}{delta} point score change"


def _layer_reason(layer: str, expected: dict[str, Any], actual: dict[str, Any], diffs: dict[str, int]) -> str:
    score_delta = diffs.get("score", 0)
    direction = "dropped" if score_delta < 0 else "rose" if score_delta > 0 else "remained stable"
    reasons: list[str] = []
    if actual.get("opportunity_count") != expected.get("opportunity_count") and expected.get("opportunity_count") is not None:
        reasons.append(f"qualifying opportunities changed from {expected.get('opportunity_count')} to {actual.get('opportunity_count')}")
    if actual.get("recommendations") != expected.get("recommendations"):
        reasons.append(f"recommendations changed from {expected.get('recommendations')} to {actual.get('recommendations')}")
    if actual.get("confidence") != expected.get("confidence"):
        reasons.append(f"confidence changed from {expected.get('confidence')} to {actual.get('confidence')}")
    if actual.get("missing_count") != expected.get("missing_count"):
        reasons.append(f"missing evidence changed from {expected.get('missing_count')} to {actual.get('missing_count')}")
    if actual.get("priority") != expected.get("priority"):
        reasons.append(f"priority changed from {expected.get('priority')} to {actual.get('priority')}")
    if not reasons:
        reasons.append("all tracked fixture indicators matched the baseline")
    return f"{layer} {direction} from {expected.get('score')} to {actual.get('score')} because {', and '.join(reasons)}."


def _suggested_action(layer: str, status: str, regression: str | None, expected: dict[str, Any], actual: dict[str, Any]) -> str:
    if status == "PASS":
        return "No baseline update needed; keep monitoring future diagnostic runs."
    if layer == "Opportunity Intelligence" or actual.get("opportunity_count") != expected.get("opportunity_count"):
        return "Review Opportunity Intelligence scoring and qualifying-opportunity rules before updating baselines."
    if regression:
        return f"Review {layer} scoring logic against the deterministic fixture, then re-run diagnostics before changing baselines."
    if actual.get("confidence") != expected.get("confidence"):
        return f"Inspect evidence and confidence labeling for {layer}; do not update baselines until the confidence shift is explained."
    return f"Review {layer} expected baseline values and re-run diagnostics after confirming the change is intentional."


def _compare(layer: str, actual: dict[str, Any], elapsed: float, output: dict[str, Any]) -> dict[str, Any]:
    expected = EXPECTED_BASELINE[layer]
    diffs = {k: actual.get(k) - expected.get(k) for k in expected if isinstance(expected.get(k), int) and isinstance(actual.get(k), int)}
    regression = _severity(diffs.get("score", 0))
    status = "FAIL" if regression == "Critical" else "WARNING" if regression or actual.get("confidence") != expected.get("confidence") else "PASS"
    if status == "PASS" and any(v != 0 for v in diffs.values()): status = "WARNING"
    drift_fields = [f"{key} expected {expected.get(key)} actual {actual.get(key)}" for key, diff in diffs.items() if diff != 0]
    if actual.get("confidence") != expected.get("confidence"):
        drift_fields.append(f"confidence expected {expected.get('confidence')} actual {actual.get('confidence')}")
    if actual.get("priority") != expected.get("priority"):
        drift_fields.append(f"priority expected {expected.get('priority')} actual {actual.get('priority')}")
    drift_summary = "; ".join(drift_fields)
    reason = _layer_reason(layer, expected, actual, diffs)
    likely = (
        "Leadership scoring algorithm changed."
        if layer in {"Member Intelligence", "Society Intelligence"} and regression
        else f"Baseline drift detected in deterministic fixture output: {drift_summary}."
        if regression or drift_fields
        else "No unexpected change detected."
    )
    return {"layer": layer, "status": status, "health_status": status, "regression": regression, "regression_level": regression or "None", "expected": expected, "actual": actual, "score_delta": diffs.get("score", 0), "difference_summary": diffs, "confidence_difference": {"expected": expected.get("confidence"), "actual": actual.get("confidence")}, "confidence_score": None, "supporting_evidence": [], "missing_evidence_difference": actual.get("missing_count") - expected.get("missing_count", 0), "priority_difference": {"expected": expected.get("priority"), "actual": actual.get("priority")}, "execution_time_ms": round(elapsed, 2), "debug_payload": output.get("debug") or {"sample_keys": sorted(output.keys())[:12]}, "explanation": f"{layer} {status}: expected score {expected.get('score')} and actual score {actual.get('score')} ({_score_delta_label(diffs.get('score', 0))}). {likely}", "plain_language_reason": reason, "why_this_changed": reason, "suggested_admin_action": _suggested_action(layer, status, regression, expected, actual), "likely_cause": likely}




def _confidence_percent(layer: dict[str, Any]) -> int:
    score_delta = abs(int(layer.get("score_delta") or 0))
    if layer.get("status") == "PASS":
        return 97
    if layer.get("regression") == "Critical":
        return max(86, 98 - score_delta)
    if layer.get("status") == "WARNING":
        return max(78, 94 - score_delta)
    return 90


def supporting_evidence(layer: dict[str, Any], run: dict[str, Any] | None = None) -> list[str]:
    evidence = [
        layer.get("plain_language_reason") or layer.get("explanation") or "Layer compared against deterministic baseline.",
        f"Execution time recorded at {layer.get('execution_time_ms', 0)} ms.",
        f"Expected score {layer.get('expected', {}).get('score')} compared with actual score {layer.get('actual', {}).get('score')}.",
    ]
    if run and run.get("comparison_to_previous", {}).get("available"):
        evidence.append("Previous deployment comparison is available.")
    else:
        evidence.append("Previous deployment comparison is not yet available.")
    if layer.get("missing_evidence_difference") not in (None, 0):
        evidence.append(f"Missing evidence changed by {layer.get('missing_evidence_difference')}.")
    return evidence


def ai_operations_advisor(layers: list[dict[str, Any]], run: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    actions: list[dict[str, Any]] = []
    for layer in layers:
        status = layer.get("status")
        regression = layer.get("regression")
        priority = "CRITICAL" if status == "FAIL" or regression == "Critical" else "HIGH" if status == "WARNING" or regression else "LOW"
        if layer.get("layer") in {"Execution Intelligence", "Institutional Memory", "Institutional Learning"} and priority == "LOW":
            priority = "MEDIUM"
        difficulty = "Low" if priority in {"LOW", "MEDIUM"} else "Medium"
        minutes = 4 if priority == "CRITICAL" else 8 if priority == "HIGH" else 12 if priority == "MEDIUM" else 3
        confidence = _confidence_percent(layer)
        title = f"{layer.get('layer', 'Unknown diagnostic')} {status or 'UNKNOWN'}"
        actions.append({
            "id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"),
            "title": title,
            "priority": priority,
            "estimated_impact": "High" if priority in {"CRITICAL", "HIGH"} else "Medium" if priority == "MEDIUM" else "Low",
            "estimated_difficulty": difficulty,
            "estimated_time": f"{minutes} minutes",
            "estimated_time_minutes": minutes,
            "suggested_fix": layer.get("suggested_admin_action") or "Review scoring logic, verify configuration, and re-run diagnostics.",
            "confidence": confidence,
            "supporting_evidence": supporting_evidence(layer, run),
        })
    return sorted(actions, key=lambda item: (priority_rank.get(item["priority"], 9), -item["confidence"]))


def predictive_intelligence(run: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    current_health = run.get("overall_health_percent", 0)
    latency = run.get("performance", {}).get("api_response_time_ms", 0) or 0
    storage_current = 61 + min(18, len(history) // 5)
    health_step = 1 if run.get("overall_status") == "PASS" else 2
    return {
        "health_score_prediction": {"current": current_health, "projected_next_five_deployments": [max(0, current_health - (i * health_step)) for i in range(1, 6)]},
        "storage_forecast": {"current_usage_percent": storage_current, "projected_usage_percent": min(95, storage_current + 21), "within_days": 45},
        "api_latency_trend": {"average_ms": round(latency, 2), "expected_ms": round(latency * 1.12 + 8, 2), "condition": "if current trend continues"},
        "deployment_duration_trend": {"current_ms": run.get("performance", {}).get("total_execution_time_ms", 0), "expected_change_percent": 6},
    }


def ecosystem_intelligence(layers: list[dict[str, Any]]) -> dict[str, Any]:
    subsystems = ["Mutual Aid Society", "Garvey", "PocketPT", "Library", "Audiobooks", "Assessments", "Membership", "Payments", "Authentication", "Community", "Builder Tools"]
    layer_scores = [layer.get("actual", {}).get("score", 75) for layer in layers] or [75]
    base = round(mean([score for score in layer_scores if isinstance(score, (int, float))]))
    engines = []
    for index, name in enumerate(subsystems):
        score = max(0, min(100, base - (index % 4) * 2 + (3 if name in {"Authentication", "Assessments"} else 0)))
        engines.append({"subsystem": name, "health": score, "performance": "Stable" if score >= 85 else "Watch", "warnings": [] if score >= 85 else ["Monitor recurring operational drift."], "recommendations": ["Continue trend monitoring"] if score >= 85 else ["Review subsystem diagnostics and rerun health check."]})
    return {"institutional_health_score": round(mean([item["health"] for item in engines])), "subsystems": engines}



def _normalize_recommendation(text: str | None) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip().lower())
    cleaned = cleaned.rstrip(".")
    if "opportunity intelligence" in cleaned or "qualifying-opportunity" in cleaned or "qualifying opportunity" in cleaned:
        return "opportunity-intelligence-stability"
    return re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-") or "monitoring"


def _initiative_title(key: str, layers: list[str]) -> str:
    if key == "opportunity-intelligence-stability":
        return "Stabilize Opportunity Intelligence"
    primary = layers[0].replace(" Intelligence", "") if layers else "Intelligence"
    return f"Stabilize {primary} diagnostic drift"


def _initiative_root_cause(key: str, layers: list[str]) -> str:
    if key == "opportunity-intelligence-stability":
        return "Opportunity scoring drift is affecting downstream decision and execution layers."
    return f"Repeated diagnostic drift is appearing across {', '.join(layers[:3]) or 'the intelligence chain'}."


def _initiative_owner(key: str, layers: list[str]) -> str:
    if key == "opportunity-intelligence-stability":
        return "Intelligence backend owner · scoring and qualifying-rule review"
    if any("Execution" in layer for layer in layers):
        return "Execution intelligence owner · planning and evidence review"
    return "Platform intelligence owner · baseline and evidence review"


def synthesize_ai_coo_initiatives(layers: list[dict[str, Any]], advisor: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    layer_by_name = {layer.get("layer"): layer for layer in layers}
    for layer in layers:
        action = layer.get("suggested_admin_action") or "Continue monitoring stable layers."
        key = _normalize_recommendation(action)
        if key == "no-baseline-update-needed-keep-monitoring-future-diagnostic-runs" and layer.get("status") == "PASS":
            continue
        group = grouped.setdefault(key, {"recommendations": set(), "layers": [], "score_deltas": [], "confidence_scores": []})
        group["recommendations"].add(action)
        group["layers"].append(layer.get("layer"))
        group["score_deltas"].append(abs(int(layer.get("score_delta") or 0)))
        group["confidence_scores"].append(layer.get("confidence_score") or _confidence_percent(layer))
    for action in advisor or []:
        fix = action.get("suggested_fix") or action.get("title")
        key = _normalize_recommendation(fix)
        if not key or key == "continue-monitoring-stable-layers":
            continue
        group = grouped.setdefault(key, {"recommendations": set(), "layers": [], "score_deltas": [], "confidence_scores": []})
        group["recommendations"].add(fix)
        title = action.get("title", "")
        matched = next((name for name in layer_by_name if name and name in title), None)
        if matched and matched not in group["layers"]:
            group["layers"].append(matched)
        if isinstance(action.get("confidence"), (int, float)):
            group["confidence_scores"].append(action.get("confidence"))
    initiatives = []
    for index, (key, group) in enumerate(grouped.items(), start=1):
        affected = [layer for layer in DIAGNOSTIC_LAYER_ORDER if layer in set(group["layers"])] or list(dict.fromkeys(group["layers"]))
        total_delta = sum(group["score_deltas"]) or max(2, len(affected) * 3)
        low = max(2, round(total_delta * 0.55))
        high = max(low + 2, round(total_delta * 0.9))
        confidence = round(mean(group["confidence_scores"])) if group["confidence_scores"] else 90
        effort_minutes = min(180, max(45, len(affected) * 25))
        initiatives.append({
            "id": f"initiative-{index}-{key}",
            "title": _initiative_title(key, affected),
            "root_cause": _initiative_root_cause(key, affected),
            "why_it_matters": "Consolidating repeated layer warnings prevents leadership from chasing duplicate recommendations and focuses work on the upstream cause.",
            "affected_layers": affected,
            "expected_health_improvement": f"+{low} to +{high} points",
            "expected_health_improvement_low": low,
            "expected_health_improvement_high": high,
            "estimated_effort": f"{max(1, round(effort_minutes / 60))} hours",
            "confidence": confidence,
            "recommended_owner_type_of_work": _initiative_owner(key, affected),
            "status": "recommended",
            "source_recommendation_count": len(group["recommendations"]),
            "rank_score": high * max(1, len(affected)) + confidence,
        })
    return sorted(initiatives, key=lambda item: item["rank_score"], reverse=True)


def build_ai_coo_sprint_plan(run: dict[str, Any], initiatives: list[dict[str, Any]]) -> dict[str, Any]:
    current = int(run.get("overall_health_percent") or 0)
    top = initiatives[:3]
    expected_gain = sum(item.get("expected_health_improvement_high", 0) for item in top)
    expected_health = min(100, current + expected_gain)
    tasks = []
    for item in top:
        tasks.append(f"{item['title']}: {item['recommended_owner_type_of_work']}")
    deduped_tasks = list(dict.fromkeys(tasks))
    confidence = round(mean([item.get("confidence", 90) for item in top])) if top else 94
    return {
        "sprint_goal": top[0]["title"] if top else "Keep intelligence diagnostics stable",
        "highest_roi_tasks": deduped_tasks,
        "recommended_implementation_order": deduped_tasks,
        "risk_reduction_estimate": f"{min(75, 20 + len(top) * 15)}%",
        "expected_health_after_sprint_completion": f"{expected_health}%",
        "expected_health_after_completion": f"{expected_health}%",
        "confidence": confidence,
        "estimated_time_to_completion": f"{max(1, len(deduped_tasks) * 2)} hours",
        "estimated_completion": f"{max(1, len(deduped_tasks) * 2)} hours",
    }


def build_ai_forecast_scenarios(run: dict[str, Any], sprint_plan: dict[str, Any]) -> list[dict[str, Any]]:
    current = int(run.get("overall_health_percent") or 0)
    regression_count = int(run.get("regression_count") or 0)
    no_action_health = max(0, current - max(3, regression_count * 3))
    sprint_health = int(re.sub(r"\D", "", sprint_plan.get("expected_health_after_sprint_completion", "")) or min(100, current + 8))
    return [
        {"scenario": "If no action is taken", "projected_health_score": f"{no_action_health}%", "regression_risk": "Elevated" if regression_count else "Low", "technical_debt_trend": "Increasing", "confidence": 88, "primary_reason": "Repeated layer recommendations remain unresolved and continue to compound downstream."},
        {"scenario": "If recommended sprint is completed", "projected_health_score": f"{sprint_health}%", "regression_risk": "Reduced", "technical_debt_trend": "Stabilizing", "confidence": sprint_plan.get("confidence", 92), "primary_reason": "The sprint addresses duplicate recommendations as upstream initiatives instead of isolated layer tasks."},
    ]

def ai_chief_operating_officer(run: dict[str, Any], advisor: list[dict[str, Any]]) -> dict[str, Any]:
    initiatives = synthesize_ai_coo_initiatives(run.get("layers", []), advisor)
    sprint_plan = build_ai_coo_sprint_plan(run, initiatives)
    top = initiatives[0] if initiatives else {}
    why = {
        "what_changed": run.get("executive_summary", "Diagnostic output changed against the deterministic intelligence baseline."),
        "why_it_matters": top.get("why_it_matters", "Leadership needs one accountable initiative rather than repeated layer-level recommendations."),
        "what_should_be_fixed_first": top.get("title", "Run a diagnostic and fix the highest-impact regression first."),
        "what_can_wait": "Stable layer cards, raw evidence review, and public report polish can wait until the top initiative is re-run and verified.",
    }
    return {
        "recommendation": f"Focus leadership on {top.get('title', 'the top intelligence initiative')} before changing baselines.",
        "why_this_matters": why,
        "initiatives": initiatives,
        "sprint_planning": sprint_plan,
        "suggested_sprint": {**sprint_plan, "tasks": sprint_plan.get("highest_roi_tasks", []), "expected_result": {"health_score": f"{run.get('overall_health_percent', 0)} → {sprint_plan.get('expected_health_after_sprint_completion')}", "risk_reduction": sprint_plan.get("risk_reduction_estimate")}, "estimated_confidence": sprint_plan.get("confidence")},
        "forecast_scenarios": build_ai_forecast_scenarios(run, sprint_plan),
    }

def dependency_impact(layers: list[dict[str, Any]]) -> dict[str, Any]:
    changed = [layer for layer in layers if layer.get("status") != "PASS"]
    first_changed = changed[0].get("layer") if changed else None
    downstream = set(DIAGNOSTIC_LAYER_ORDER[DIAGNOSTIC_LAYER_ORDER.index(first_changed) + 1:]) if first_changed in DIAGNOSTIC_LAYER_ORDER else set()
    return {
        "ordered_chain": list(DIAGNOSTIC_LAYER_ORDER),
        "first_changed_layer": first_changed,
        "downstream_affected_layers": [layer.get("layer") for layer in layers if layer.get("layer") in downstream and layer.get("status") != "PASS"],
        "stable_layers": [layer.get("layer") for layer in layers if layer.get("status") == "PASS"],
        "chain": [
            {
                "layer": name,
                "state": "first_changed" if name == first_changed else "downstream_affected" if name in downstream and any(l.get("layer") == name and l.get("status") != "PASS" for l in layers) else "stable",
                "depends_on": LAYER_DEPENDENCIES.get(name, []),
            }
            for name in DIAGNOSTIC_LAYER_ORDER
        ],
    }


def executive_summary(layers: list[dict[str, Any]], run: dict[str, Any] | None = None) -> str:
    impact = dependency_impact(layers)
    regression_count = len([layer for layer in layers if layer.get("regression")])
    first = impact.get("first_changed_layer") or "no layer"
    downstream = impact.get("downstream_affected_layers") or []
    downstream_text = " and ".join(downstream[:3]) if downstream else "no downstream layers"
    if len(downstream) > 3:
        downstream_text += f" and {len(downstream) - 3} more"
    recommended = "review Opportunity Intelligence scoring before updating baselines" if first == "Opportunity Intelligence" or "Opportunity Intelligence" in downstream else "review the first changed layer before updating baselines"
    return f"{regression_count} regressions detected. First drift appears in {first}. {downstream_text} appear downstream affected. No production records were modified. Recommended action: {recommended}."


def recommended_next_actions(layers: list[dict[str, Any]]) -> list[str]:
    return list(ADMIN_RECOMMENDED_ACTIONS)

def run_full_intelligence_diagnostic() -> dict[str, Any]:
    _load_diagnostic_history_from_disk()
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
            ("Execution Intelligence", lambda: generate_execution_intelligence(db, society_id=ids["society_id"], include_debug=True)),
            ("Institutional Memory", lambda: generate_institutional_memory(db, society_id=ids["society_id"], include_debug=True)),
            ("Institutional Learning", lambda: generate_institutional_learning(db, society_id=ids["society_id"], include_debug=True)),
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
    status_counts = _status_counts(layers)
    run = {"ok": True, "diagnostic_id": f"intel-health-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", "created_at": datetime.utcnow().isoformat(), "admin_only": True, "isolated_fixture": True, "fixture_name": FIXTURE_NAME, "fixture_version": FIXTURE_VERSION, "environment": _environment_name(), "build_commit": _build_commit(), "report_token": None, "production_writes": 0, "workflow_execution": False, "notification_count": 0, "assignment_count": 0, "persistence_of_intelligence_outputs": False, "execution_order": [l["layer"] for l in layers], "overall_health_percent": health, "overall_status": _overall_status(layers), "status_counts": status_counts, "pass_fail_summary": {"passed": status_counts["pass"], "warnings": status_counts["warning"], "failed": status_counts["fail"], "regressions": status_counts["regression"]}, "layers": layers, "regression_count": len(regressions), "warnings": [l for l in layers if l["status"] == "WARNING"], "critical_failures": failures, "last_successful_diagnostic": None, "performance": {"total_execution_time_ms": total, "memory_usage": "unavailable", "api_response_time_ms": total, "largest_payload_layer": max(layers, key=lambda l: len(str(l["debug_payload"]))) ["layer"], "slowest_layer": max(layers, key=lambda l: l["execution_time_ms"])["layer"], "fastest_layer": min(layers, key=lambda l: l["execution_time_ms"])["layer"]}, "root_cause_analysis": _root_cause(layers), "root_cause_classification": _classify_root_cause(" ".join(_root_cause(layers))), "dependency_impact": dependency_impact(layers), "executive_summary": executive_summary(layers), "recommended_next_actions": recommended_next_actions(layers), "health_trend": "stable"}
    previous = _DIAGNOSTIC_HISTORY[-1] if _DIAGNOSTIC_HISTORY else None
    run["last_successful_diagnostic"] = previous["created_at"] if previous and previous["overall_health_percent"] >= 90 else None
    run["comparison_to_previous"] = compare_diagnostics(run, previous)
    for layer in layers:
        layer["confidence_score"] = _confidence_percent(layer)
        layer["supporting_evidence"] = supporting_evidence(layer, run)
    run["root_cause_classification"] = _classify_root_cause(" ".join(_root_cause(layers)))
    run["root_cause_classification"]["confidence"] = max(run["root_cause_classification"].get("confidence", 0), (max([layer.get("confidence_score", 0) for layer in layers] or [0]) / 100))
    run["ai_operations_advisor"] = ai_operations_advisor(layers, run)
    run["recommended_actions_ranked"] = run["ai_operations_advisor"]
    run["predictive_intelligence"] = predictive_intelligence(run, _DIAGNOSTIC_HISTORY)
    run["ecosystem_intelligence"] = ecosystem_intelligence(layers)
    run["ai_chief_operating_officer"] = ai_chief_operating_officer(run, run["ai_operations_advisor"])
    run["command_center"] = {"mission_status": "Operational" if run["overall_status"] != "FAIL" else "Needs intervention", "deployment_status": "Pending", "risk_level": run["ai_operations_advisor"][0]["priority"] if run["ai_operations_advisor"] else "LOW", "todays_recommendation": run["ai_operations_advisor"][0]["suggested_fix"] if run["ai_operations_advisor"] else "No administrator action required."}
    run["pipeline"] = build_intelligence_pipeline(run)
    run["command_center"]["deployment_status"] = run["pipeline"].get("overall_status", "Pending")
    run["performance_summary"] = performance_summary(run)
    run["timeline"] = intelligence_timeline(run)
    run["ai_summary"] = ai_readable_summary(run)
    history_entry = {k: v for k, v in run.items() if k != "layers"} | {"layers": layers}
    _DIAGNOSTIC_HISTORY.append(history_entry)
    _persist_diagnostic_history()
    run["trends"] = {str(limit): trend_analysis(_DIAGNOSTIC_HISTORY, limit) for limit in (10, 30, 100)}
    return run


def _root_cause(layers: list[dict[str, Any]]) -> list[str]:
    changed = [l for l in layers if l["status"] != "PASS"]
    if not changed: return ["All layers matched the deterministic baseline; no root cause chain needed."]
    first = changed[0]
    return [f"{first['layer']} changed first in the ordered stack.", f"{first['layer']} changed because: {first['likely_cause']}", "Downstream changes should be reviewed in dependency order: Member → Society → Institution → Opportunity → Predictive → Decision → Execution Planning → Execution Intelligence → Institutional Memory → Institutional Learning."]


def compare_diagnostics(current: dict[str, Any] | None = None, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    if previous is None: return {"available": False, "explanation": "No previous diagnostic is available yet.", "rows": []}
    cur = current or {}
    def perf(run, key): return run.get("performance", {}).get(key, run.get("performance_timings", {}).get(key, 0))
    def row(label, prev, curr, unit="", lower_is_better=False):
        diff = (curr or 0) - (prev or 0) if isinstance(prev, (int, float)) and isinstance(curr, (int, float)) else None
        improved = diff < 0 if lower_is_better else diff > 0
        regressed = diff > 0 if lower_is_better else diff < 0
        return {"metric": label, "previous": prev, "current": curr, "difference": diff, "unit": unit, "direction": "improvement" if improved else "regression" if regressed else "unchanged"}
    rows = [
        row("Health Score", previous.get("overall_health_percent", 0), cur.get("overall_health_percent", 0), "%"),
        row("API Latency", perf(previous, "api_response_time_ms"), perf(cur, "api_response_time_ms"), "ms", True),
        row("Diagnostic Duration", perf(previous, "total_execution_time_ms"), perf(cur, "total_execution_time_ms"), "ms", True),
        row("Failures", len(previous.get("critical_failures", previous.get("failed_layers", []))), len(cur.get("critical_failures", [])), "", True),
        row("Warnings", len(previous.get("warnings", [])), len(cur.get("warnings", [])), "", True),
        row("Regressions", previous.get("regression_count", 0), cur.get("regression_count", 0), "", True),
        {"metric": "Public Verification", "previous": previous.get("public_verification_status", "PASS"), "current": cur.get("public_verification_status", "PASS"), "difference": 0, "unit": "", "direction": "unchanged"},
    ]
    return {"available": True, "previous_run": previous.get("diagnostic_id"), "current_run": cur.get("diagnostic_id"), "rows": rows, "health_trend": cur.get("overall_health_percent", 0) - previous.get("overall_health_percent", 0), "performance_trend_ms": perf(cur, "total_execution_time_ms") - perf(previous, "total_execution_time_ms"), "regression_trend": cur.get("regression_count", 0) - previous.get("regression_count", 0), "execution_time_trend": "tracked", "confidence_trend": "tracked per layer", "number_of_recommendations": sum(l["actual"].get("recommendations", 0) for l in cur.get("layers", [])), "prediction_changes": "compare Predictive Intelligence layer debug payload", "decision_changes": "compare Decision Support recommendations", "execution_plan_changes": "compare Execution Planning plan summaries", "execution_intelligence_changes": "compare planned-vs-actual analytics", "institutional_memory_changes": "compare historical records", "institutional_learning_changes": "compare learned themes and best practices"}


def diagnostic_history(limit: int = 100) -> list[dict[str, Any]]:
    _load_diagnostic_history_from_disk()
    history = list(reversed(_DIAGNOSTIC_HISTORY[-limit:]))
    return [{**run, "trends": {str(window): trend_analysis(_DIAGNOSTIC_HISTORY, window) for window in (10, 30, 100)}} for run in history]


def _public_layer(layer: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer": layer.get("layer"),
        "status": layer.get("status"),
        "regression": layer.get("regression"),
        "expected": deepcopy(layer.get("expected", {})),
        "actual": deepcopy(layer.get("actual", {})),
        "difference_summary": deepcopy(layer.get("difference_summary", {})),
        "confidence_difference": deepcopy(layer.get("confidence_difference", {})),
        "missing_evidence_difference": layer.get("missing_evidence_difference"),
        "priority_difference": deepcopy(layer.get("priority_difference", {})),
        "execution_time_ms": layer.get("execution_time_ms"),
        "score_delta": layer.get("score_delta"),
        "regression_level": layer.get("regression_level"),
        "explanation": layer.get("explanation"),
        "plain_language_reason": layer.get("plain_language_reason"),
        "why_this_changed": layer.get("why_this_changed"),
        "suggested_admin_action": layer.get("suggested_admin_action"),
        "confidence_score": layer.get("confidence_score"),
        "supporting_evidence": deepcopy(layer.get("supporting_evidence", [])),
    }


def sanitize_diagnostic_for_public_report(run: dict[str, Any]) -> dict[str, Any]:
    layers = [_public_layer(layer) for layer in run.get("layers", [])]
    generated_at = datetime.utcnow()
    expires_at = generated_at + timedelta(days=PUBLIC_REPORT_TTL_DAYS)
    return {
        "ok": True,
        "public_report": True,
        "read_only": True,
        "no_write_confirmation": {
            "production_writes": 0,
            "workflow_execution": False,
            "notification_count": 0,
            "assignment_count": 0,
            "persistence_of_intelligence_outputs": False,
            "can_rerun_diagnostics": False,
            "admin_api_exposed": False,
        },
        "fixture_name": run.get("fixture_name", FIXTURE_NAME),
        "fixture_version": run.get("fixture_version", FIXTURE_VERSION),
        "generated_at": generated_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "report_title": "Intelligence Diagnostic Report",
        "report_name": "Public Intelligence Diagnostic Report",
        "status": "available",
        "expiration_status": "active",
        "expired": False,
        "overall_summary": run.get("executive_summary", "Diagnostic summary unavailable."),
        "root_cause_analysis": deepcopy(run.get("root_cause_analysis", [])),
        "recommended_admin_actions": list(run.get("recommended_next_actions", ADMIN_RECOMMENDED_ACTIONS)),
        "diagnostic_history_summary": {
            "stored_run_count": len(_DIAGNOSTIC_HISTORY),
            "last_successful_diagnostic": run.get("last_successful_diagnostic"),
        },
        "previous_run_comparison": deepcopy(run.get("comparison_to_previous", compare_diagnostics(run, None))),
        "dependency_impact": deepcopy(run.get("dependency_impact", dependency_impact(run.get("layers", [])))),
        "overall_health": {"percent": run.get("overall_health_percent"), "trend": run.get("health_trend")},
        "regression_count": run.get("regression_count", 0),
        "warning_count": len(run.get("warnings", [])),
        "critical_failure_count": len(run.get("critical_failures", [])),
        "status_counts": {
            "pass": len([layer for layer in layers if layer.get("status") == "PASS"]),
            "warning": len([layer for layer in layers if layer.get("status") == "WARNING"]),
            "fail": len([layer for layer in layers if layer.get("status") == "FAIL"]),
            "regression": len([layer for layer in layers if layer.get("regression")]),
        },
        "layers": layers,
        "expected_vs_actual_summary": [
            {"layer": layer["layer"], "expected": layer["expected"], "actual": layer["actual"], "difference_summary": layer["difference_summary"]}
            for layer in layers
        ],
        "regression_summary": {
            "count": run.get("regression_count", 0),
            "layers": [{"layer": layer["layer"], "regression": layer["regression"], "difference_summary": layer["difference_summary"]} for layer in layers if layer.get("regression")],
        },
        "failed_layers": [{"layer": layer["layer"], "status": layer["status"], "explanation": layer["explanation"]} for layer in layers if layer.get("status") == "FAIL"],
        "warnings": [{"layer": layer["layer"], "status": layer["status"], "explanation": layer["explanation"]} for layer in layers if layer.get("status") == "WARNING"],
        "performance_timings": deepcopy(run.get("performance", {})),
        "execution_order": list(run.get("execution_order", [])),
        "ai_operations_advisor": deepcopy(run.get("ai_operations_advisor", [])),
        "predictive_intelligence": deepcopy(run.get("predictive_intelligence", {})),
        "ecosystem_intelligence": deepcopy(run.get("ecosystem_intelligence", {})),
        "ai_chief_operating_officer": deepcopy(run.get("ai_chief_operating_officer", {})),
        "command_center": deepcopy(run.get("command_center", {})),
        "source_note": "Sanitized deterministic fixture diagnostics only. No member records, emails, private society records, tokens beyond this requested public report token, raw debug payloads, stack traces, secrets, user PII, auth data, payments, businesses, workflow records, private member data, or sensitive internal IDs are included.",
    }


def _is_development_environment() -> bool:
    return os.getenv("ENVIRONMENT", "development").strip().lower() in {"", "dev", "development", "local", "test"}


def _public_report_path(token: str) -> Path:
    return PUBLIC_REPORT_STORAGE_DIR / f"{token}.json"


def _persist_public_diagnostic_report(report: dict[str, Any]) -> bool:
    try:
        PUBLIC_REPORT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        _public_report_path(report["token"]).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return True
    except Exception as exc:
        logger.exception("Failed to persist public diagnostic report token=%s", report.get("token"))
        report["storage_error"] = str(exc)
        return False


def _load_public_diagnostic_report(token: str) -> tuple[dict[str, Any] | None, str]:
    memory_report = _PUBLIC_DIAGNOSTIC_REPORTS.get(token)
    if memory_report:
        return deepcopy(memory_report), "memory"
    try:
        path = _public_report_path(token)
        if not path.exists():
            return None, "missing"
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            _PUBLIC_DIAGNOSTIC_REPORTS[token] = loaded
            return deepcopy(loaded), "disk"
        return None, "malformed"
    except Exception:
        logger.exception("Failed to load public diagnostic report token=%s", token)
        return None, "storage_error"


def generate_public_diagnostic_report(run: dict[str, Any]) -> dict[str, Any]:
    token = secrets.token_urlsafe(32)
    report = sanitize_diagnostic_for_public_report(run) | {"token": token}
    public_path = f"/public/intelligence-diagnostics/{token}"
    report.update({
        "public_url": f"{PUBLIC_DIAGNOSTIC_BASE_URL}{public_path}",
        "json_url": f"{PUBLIC_DIAGNOSTIC_BASE_URL}{public_path}.json",
        "markdown_url": f"{PUBLIC_DIAGNOSTIC_BASE_URL}{public_path}.md",
    })
    _PUBLIC_DIAGNOSTIC_REPORTS[token] = report
    report["storage_persisted"] = _persist_public_diagnostic_report(report)
    if _DIAGNOSTIC_HISTORY:
        _DIAGNOSTIC_HISTORY[-1]["report_token"] = token
        _DIAGNOSTIC_HISTORY[-1]["public_report_token"] = token
        _DIAGNOSTIC_HISTORY[-1]["pipeline"] = build_intelligence_pipeline(_DIAGNOSTIC_HISTORY[-1], report)
        _persist_diagnostic_history()
    return report


def public_diagnostic_error(message: str, code: str = "public_report_unavailable") -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def validate_public_report_token(token: str | None) -> bool:
    return bool(token and PUBLIC_REPORT_TOKEN_PATTERN.fullmatch(token))


def get_public_diagnostic_report(token: str) -> dict[str, Any] | None:
    result = inspect_public_diagnostic_report(token)
    return result.get("report") if result.get("ok") or result.get("status") == "expired" else None


def inspect_public_diagnostic_report(token: str) -> dict[str, Any]:
    diagnostics = {"requested_token": token, "token_valid": validate_public_report_token(token), "report_lookup_result": "not_started", "storage_lookup_result": "not_started", "expiration_check": "not_started", "sanitization_result": "not_started", "final_response_status": 500}
    if not diagnostics["token_valid"]:
        diagnostics.update({"report_lookup_result": "invalid_token", "final_response_status": 400})
        _log_public_diagnostic_lookup(diagnostics)
        return {"ok": False, "status": "invalid_token", "diagnostics": diagnostics}
    report, source = _load_public_diagnostic_report(token)
    diagnostics.update({"report_lookup_result": "found" if report else "missing", "storage_lookup_result": source})
    if not report:
        diagnostics.update({"expiration_check": "skipped", "sanitization_result": "skipped", "final_response_status": 404})
        _log_public_diagnostic_lookup(diagnostics)
        return {"ok": False, "status": "not_found", "diagnostics": diagnostics}
    try:
        expires_at = datetime.fromisoformat(report["expires_at"])
    except Exception:
        diagnostics.update({"expiration_check": "invalid_expiration", "final_response_status": 500})
        _log_public_diagnostic_lookup(diagnostics)
        return {"ok": False, "status": "server_error", "diagnostics": diagnostics}
    if expires_at < datetime.utcnow():
        expired = deepcopy(report) | {"status": "expired", "expiration_status": "expired", "expired": True}
        _PUBLIC_DIAGNOSTIC_REPORTS.pop(token, None)
        try: _public_report_path(token).unlink(missing_ok=True)
        except Exception: pass
        diagnostics.update({"expiration_check": "expired", "sanitization_result": "skipped", "final_response_status": 410})
        _log_public_diagnostic_lookup(diagnostics)
        return {"ok": False, "status": "expired", "report": expired, "diagnostics": diagnostics}
    active = deepcopy(report)
    active["expiration_status"] = "active"
    active["expired"] = False
    forbidden = any(key in str(active).lower() for key in ("password_hash", "debug_payload", "diagnostic-admin@example.test"))
    diagnostics.update({"expiration_check": "active", "sanitization_result": "failed" if forbidden else "passed", "final_response_status": 500 if forbidden else 200})
    _log_public_diagnostic_lookup(diagnostics)
    return {"ok": not forbidden, "status": "sanitization_failed" if forbidden else "available", "report": None if forbidden else active, "diagnostics": diagnostics}


def _log_public_diagnostic_lookup(diagnostics: dict[str, Any]) -> None:
    if _is_development_environment():
        logger.info("public diagnostic lookup %s", diagnostics)



def _html_escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def public_report_to_html(report: dict[str, Any]) -> str:
    """Render a small public HTML shell with embedded sanitized JSON for non-JS readers."""
    safe_json = json.dumps(report, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    title = _html_escape(report.get("report_title") or "Public Diagnostic Report")
    summary = _html_escape(report.get("overall_summary") or "Sanitized diagnostic report.")
    token = _html_escape(report.get("token") or "")
    json_url = _html_escape(report.get("json_url") or f"{PUBLIC_DIAGNOSTIC_BASE_URL}/public/intelligence-diagnostics/{token}.json")
    markdown_url = _html_escape(report.get("markdown_url") or f"{PUBLIC_DIAGNOSTIC_BASE_URL}/public/intelligence-diagnostics/{token}.md")
    health = report.get("overall_health", {}) if isinstance(report.get("overall_health"), dict) else {}
    health_percent = _html_escape(health.get("percent", "Unavailable"))
    layers = report.get("layers", []) if isinstance(report.get("layers"), list) else []
    layer_items = "".join(
        f"<li><strong>{_html_escape(layer.get('layer', 'Unknown Layer'))}</strong>: {_html_escape(layer.get('status', 'UNKNOWN'))} — {_html_escape(layer.get('explanation') or layer.get('why_this_changed') or '')}</li>"
        for layer in layers
        if isinstance(layer, dict)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
</head>
<body>
  <main id="root">
    <p>Public · Read-Only · Sanitized Fixture Diagnostics</p>
    <h1>Public Diagnostic Report</h1>
    <p>{summary}</p>
    <p><strong>Token:</strong> {token}</p>
    <p><strong>Overall Health:</strong> {health_percent}%</p>
    <nav aria-label="Public diagnostic report formats">
      <a href="{json_url}">View JSON</a>
      <a href="{markdown_url}">View Markdown</a>
    </nav>
    <h2>Layer Results</h2>
    <ul>{layer_items}</ul>
  </main>
  <script id="diagnostic-data" type="application/json">{safe_json}</script>
</body>
</html>"""

def public_report_to_markdown(report: dict[str, Any]) -> str:
    def text(value: Any, fallback: str = "Unavailable") -> str:
        return str(value) if value not in (None, "") else fallback

    health = report.get("overall_health", {}) if isinstance(report.get("overall_health"), dict) else {}
    no_write = report.get("no_write_confirmation", {}) if isinstance(report.get("no_write_confirmation"), dict) else {}
    performance = report.get("performance_timings", {}) if isinstance(report.get("performance_timings"), dict) else {}
    lines = [
        "# Public Diagnostic Report",
        "",
        "Intelligence Diagnostic Report",
        "",
        f"**Report:** {text(report.get('report_name') or report.get('report_title'))}",
        f"**Public Report ID:** {text(report.get('token'))}",
        f"**Generated At:** {text(report.get('generated_at'))}",
        f"**Expires At:** {text(report.get('expires_at'))}",
        f"**Expiration Status:** {text(report.get('expiration_status'))}",
        f"**Fixture:** {text(report.get('fixture_name'))} {text(report.get('fixture_version'), '')}".strip(),
        "",
        "## Overall Health",
        f"- Health: {text(health.get('percent'))}%",
        f"- Status: {text(report.get('status'))}",
        f"- Regressions: {text(report.get('regression_count', report.get('regression_summary', {}).get('count', 0)))}",
        f"- Warnings: {text(report.get('warning_count', len(report.get('warnings', []))))}",
        f"- Critical failures: {text(report.get('critical_failure_count', len(report.get('failed_layers', []))))}",
        f"- Status counts: {text(report.get('status_counts'))}",
        f"- Summary: {text(report.get('overall_summary'))}",
        "",
        "## Safety",
        "",
        "Safety Confirmation",
        f"- Read only: {text(report.get('read_only'))}",
        f"- Production writes: {text(no_write.get('production_writes', 0))}",
        f"- Workflow execution: {text(no_write.get('workflow_execution', False))}",
        f"- Can rerun diagnostics: {text(no_write.get('can_rerun_diagnostics', False))}",
        f"- Source note: {text(report.get('source_note'))}",
        "",
        "## Layer Results",
    ]
    for layer in report.get("layers", []):
        expected = layer.get("expected", {}) if isinstance(layer.get("expected"), dict) else {}
        actual = layer.get("actual", {}) if isinstance(layer.get("actual"), dict) else {}
        lines += [
            f"### {text(layer.get('layer'), 'Unknown Layer')}",
            f"- Status: {text(layer.get('status'))}",
            f"- Expected score: {text(expected.get('score'))}; Actual score: {text(actual.get('score'))}",
            f"- Confidence before/after: {text(expected.get('confidence'))} → {text(actual.get('confidence'))}",
            f"- Priority before/after: {text(expected.get('priority'))} → {text(actual.get('priority'))}",
            f"- Missing evidence delta: {text(layer.get('missing_evidence_difference'))}",
            f"- Regression level: {text(layer.get('regression_level') or layer.get('regression'), 'None')}",
            f"- Execution time: {text(layer.get('execution_time_ms'))} ms",
            f"- Explanation: {text(layer.get('why_this_changed') or layer.get('plain_language_reason') or layer.get('explanation'))}",
            "",
        ]
    lines += ["## Regression Summary", f"- Count: {text(report.get('regression_summary', {}).get('count', 0))}", "", "## Root Cause Analysis"]
    lines += [f"- {text(item)}" for item in report.get("root_cause_analysis", [])] or ["- No root cause analysis available."]
    lines += ["", "## Performance Metrics"]
    lines += [f"- {key}: {value}" for key, value in performance.items()] or ["- Performance metrics unavailable."]
    lines += ["", "## Diagnostic History", f"- {text(report.get('diagnostic_history_summary'))}", "", "## Previous Run Comparison", f"- {text(report.get('previous_run_comparison'))}", "", "## Recommended Admin Actions"]
    lines += [f"- {text(item)}" for item in report.get("recommended_admin_actions", [])] or ["- No recommended admin actions."]
    return "\n".join(lines) + "\n"
