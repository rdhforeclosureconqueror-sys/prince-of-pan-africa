from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_auth, require_permission
from app.models import MutualAidAppeal, MutualAidAuditLog, MutualAidCategoryBudget, MutualAidCommitteeMember, MutualAidConflictDisclosure, MutualAidDecision, MutualAidDisbursement, MutualAidDisbursementStatusHistory, MutualAidFund, MutualAidMemberAcceptance, MutualAidNotification, MutualAidPolicyVersion, MutualAidReconciliationReport, MutualAidRequest, MutualAidRequestDocument, MutualAidRequestStatusHistory, MutualAidReview, User
from app.services.mutual_aid import DEFAULT_MUTUAL_AID_FUND_NAME, MUTUAL_AID_ACTIVATION_THRESHOLD, MUTUAL_AID_BUILDING_STATUS, mutual_aid_feature_flags, record_mutual_aid_notification

router = APIRouter(prefix="/mutual-aid", tags=["Mutual Aid"])

CATEGORIES = {"housing", "utilities", "food", "transportation", "medical", "childcare", "emergency", "other"}
URGENCIES = {"standard", "urgent", "emergency"}
SUPPORT_METHODS = {"direct_vendor", "member_follow_up", "resource_referral", "community_follow_up", "other"}
DECISIONS = {"approve", "partial_approve", "not_approved", "close"}
DECISION_REASON_CODES = {"eligible_need", "partial_need", "insufficient_documentation", "outside_policy", "duplicate_request", "withdrawn", "unable_to_contact", "closed_by_admin", "other"}
DECISION_STATUS = {"approve": "approved", "partial_approve": "partially_approved", "not_approved": "not_approved", "close": "closed"}
DISBURSEMENT_STATUSES = {"pending", "scheduled", "paid", "failed", "cancelled", "reversed", "needs_receipt", "closed"}
APPEAL_STATUSES = {"submitted", "under_review", "more_info_requested", "approved", "denied", "closed"}

class RequestPayload(BaseModel):
    category: str
    urgency: str = "standard"
    requested_amount: int = Field(ge=1, le=1000000)
    explanation: str = Field(min_length=20, max_length=5000)
    preferred_support_method: str
    policy_consent: bool

class AssignReviewerPayload(BaseModel):
    reviewer_user_id: int

class RecommendationPayload(BaseModel):
    recommendation: str = Field(min_length=3, max_length=64)
    notes: str = Field(min_length=3, max_length=5000)

class MoreInfoPayload(BaseModel):
    message: str = Field(min_length=3, max_length=5000)

class ConflictDisclosurePayload(BaseModel):
    disclosure: str = Field(min_length=3, max_length=5000)

class DecisionPayload(BaseModel):
    decision: str
    reason_code: str
    notes: str = Field(min_length=3, max_length=5000)
    approved_amount: int = Field(default=0, ge=0, le=1000000)
    appeal_eligible: bool = False
    appeal_deadline: datetime | None = None
    appeal_instructions: str = Field(default="", max_length=5000)

class DisbursementPayload(BaseModel):
    amount: int = Field(ge=1, le=1000000)
    status: str = "pending"
    receipt_required: bool = False
    scheduled_for: datetime | None = None
    notes: str = Field(default="", max_length=5000)

class DisbursementStatusPayload(BaseModel):
    status: str
    reason: str = Field(min_length=3, max_length=5000)

class AppealPayload(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    explanation: str = Field(min_length=20, max_length=5000)

class AppealReviewPayload(BaseModel):
    status: str
    notes: str = Field(min_length=3, max_length=5000)

class DocumentMetadataPayload(BaseModel):
    document_type: str = Field(default="supporting", max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="", max_length=128)
    file_size: int = Field(default=0, ge=0)
    storage_key: str = Field(default="", max_length=1024)




def _mutual_aid_route_paths():
    return sorted({getattr(route, "path", "") for route in router.routes if getattr(route, "path", "")})


def _live_money_route_findings():
    forbidden_terms = ("payment", "payments", "payout", "payouts", "wallet", "wallets")
    findings = []
    for path in _mutual_aid_route_paths():
        normalized = path.lower()
        matched = [term for term in forbidden_terms if term in normalized]
        if matched:
            findings.append({"path": f"/mutual-aid{path}", "matched_terms": matched})
    return findings


def _readiness_check(key, label, passed, detail):
    return {"key": key, "label": label, "passed": bool(passed), "detail": detail}


@router.get("/admin/pilot-readiness/verification")
def pilot_readiness_verification(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    flags = mutual_aid_feature_flags()
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    money_route_findings = _live_money_route_findings()
    checks = [
        _readiness_check("runtime_foundation_enabled", "Runtime foundation enabled", flags["ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION"], "ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION must be true."),
        _readiness_check("request_intake_enabled", "Request intake enabled", flags["MUTUAL_AID_REQUESTS_ENABLED"] and flags["ENABLE_MUTUAL_AID_REQUEST_INTAKE"], "MUTUAL_AID_REQUESTS_ENABLED / ENABLE_MUTUAL_AID_REQUEST_INTAKE must be true."),
        _readiness_check("review_workflow_enabled", "Review workflow enabled", flags["MUTUAL_AID_REVIEW_ENABLED"] and flags["ENABLE_MUTUAL_AID_REVIEW_WORKFLOW"], "MUTUAL_AID_REVIEW_ENABLED / ENABLE_MUTUAL_AID_REVIEW_WORKFLOW must be true."),
        _readiness_check("decision_workflow_enabled", "Decision workflow enabled", flags["MUTUAL_AID_DECISIONS_ENABLED"], "MUTUAL_AID_DECISIONS_ENABLED must be true."),
        _readiness_check("financial_controls_enabled", "Financial controls enabled", flags["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"], "MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED must be true."),
        _readiness_check("disbursement_tracking_enabled", "Disbursement tracking enabled", flags["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"], "MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED must be true."),
        _readiness_check("notifications_enabled", "Notifications enabled", flags["MUTUAL_AID_NOTIFICATIONS_ENABLED"], "MUTUAL_AID_NOTIFICATIONS_ENABLED must be true."),
        _readiness_check("appeals_enabled", "Appeals enabled", flags["MUTUAL_AID_APPEALS_ENABLED"], "MUTUAL_AID_APPEALS_ENABLED must be true."),
        _readiness_check("payments_disabled", "Payments disabled", not flags["ENABLE_MUTUAL_AID_PAYMENTS"], "ENABLE_MUTUAL_AID_PAYMENTS must remain false."),
        _readiness_check("activation_status_building", "Activation status is still Building Toward Activation", bool(fund and fund.status == MUTUAL_AID_BUILDING_STATUS), f"Expected {MUTUAL_AID_BUILDING_STATUS}."),
        _readiness_check("activation_threshold_20000", "Activation threshold is still 20000", bool(fund and fund.activation_threshold == MUTUAL_AID_ACTIVATION_THRESHOLD), f"Expected {MUTUAL_AID_ACTIVATION_THRESHOLD}."),
        _readiness_check("no_live_money_routes", "No live payment/payout/wallet routes exist", not money_route_findings, "Mutual Aid routes must not expose payment, payout, or wallet endpoints."),
    ]
    return {
        "ok": True,
        "pilot_hardening_enabled": flags["MUTUAL_AID_PILOT_HARDENING_ENABLED"],
        "ready": all(check["passed"] for check in checks),
        "activation_status": fund.status if fund else None,
        "activation_threshold": fund.activation_threshold if fund else None,
        "checks": checks,
        "money_route_findings": money_route_findings,
        "mutual_aid_routes": [f"/mutual-aid{path}" for path in _mutual_aid_route_paths()],
        "guardrails": ["No payment processors connected", "No money movement", "No payout execution", "No wallet balances", "No distributions before activation"],
    }



REQUIRED_LAUNCH_LOCK_FLAGS = (
    "ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION",
    "MUTUAL_AID_REQUESTS_ENABLED",
    "ENABLE_MUTUAL_AID_REQUEST_INTAKE",
    "MUTUAL_AID_REVIEW_ENABLED",
    "ENABLE_MUTUAL_AID_REVIEW_WORKFLOW",
    "MUTUAL_AID_DECISIONS_ENABLED",
    "MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED",
    "MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED",
    "MUTUAL_AID_NOTIFICATIONS_ENABLED",
    "MUTUAL_AID_APPEALS_ENABLED",
    "MUTUAL_AID_PILOT_HARDENING_ENABLED",
    "MUTUAL_AID_PILOT_LAUNCH_LOCK_ENABLED",
)
REQUIRED_RUNBOOK_FLAGS = REQUIRED_LAUNCH_LOCK_FLAGS + ("MUTUAL_AID_PILOT_RUNBOOK_ENABLED",)
REQUIRED_SMOKE_TEST_FLAGS = REQUIRED_RUNBOOK_FLAGS + ("MUTUAL_AID_PILOT_SMOKE_TESTS_ENABLED",)
REQUIRED_LAUNCH_LOCK_ROLES = {"reviewer", "treasurer", "governance"}
REQUIRED_LAUNCH_LOCK_TABLES = {"mutual_aid_audit_logs", "mutual_aid_request_status_history", "mutual_aid_notifications"}
SAFE_PRE_ACTIVATION_DISBURSEMENT_STATUSES = {"not_started", "pending", "scheduled", "cancelled", "reversed", "failed", "closed"}


def _table_available(db, table_name):
    return inspect(db.bind).has_table(table_name)


def _launch_lock_response(db):
    flags = mutual_aid_feature_flags()
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    money_route_findings = _live_money_route_findings()
    phase8 = pilot_readiness_verification(db=db)
    active_roles = {
        (row.role or "").strip().lower()
        for row in db.query(MutualAidCommitteeMember).filter(MutualAidCommitteeMember.status == "active").all()
    }
    missing_roles = sorted(REQUIRED_LAUNCH_LOCK_ROLES - active_roles)
    missing_tables = sorted(table for table in REQUIRED_LAUNCH_LOCK_TABLES if not _table_available(db, table))
    policy_count = db.query(MutualAidPolicyVersion).count() if _table_available(db, "mutual_aid_policy_versions") else 0
    acceptance_count = db.query(MutualAidMemberAcceptance).count() if _table_available(db, "mutual_aid_member_acceptances") else 0
    unsafe_distribution_count = db.query(MutualAidDisbursement).filter(~MutualAidDisbursement.status.in_(SAFE_PRE_ACTIVATION_DISBURSEMENT_STATUSES)).count()
    missing_flags = [key for key in REQUIRED_LAUNCH_LOCK_FLAGS if not flags.get(key)]
    checks = [
        _readiness_check("phase8_readiness_passes", "Phase 8 readiness passes", phase8["ready"], "Existing Phase 8 readiness verification must pass."),
        _readiness_check("payments_disabled", "Payments remain disabled", not flags["ENABLE_MUTUAL_AID_PAYMENTS"], "ENABLE_MUTUAL_AID_PAYMENTS must remain false."),
        _readiness_check("fund_building", "Fund status remains Building Toward Activation", bool(fund and fund.status == MUTUAL_AID_BUILDING_STATUS), f"Expected {MUTUAL_AID_BUILDING_STATUS}."),
        _readiness_check("no_distributions_before_activation", "No distributions before activation", unsafe_distribution_count == 0, "No paid/completed Mutual Aid distributions may exist before activation."),
        _readiness_check("policies_acknowledged", "Required docs/policies are acknowledged", policy_count > 0 and acceptance_count > 0, "At least one Mutual Aid policy version and member acceptance must be recorded."),
        _readiness_check("roles_exist", "Committee/reviewer/treasurer/governance roles exist", not missing_roles, f"Missing roles: {', '.join(missing_roles) or 'none'}."),
        _readiness_check("tables_available", "Audit/status-history/notification tables are available", not missing_tables, f"Missing tables: {', '.join(missing_tables) or 'none'}."),
        _readiness_check("required_flags_present", "Required launch-lock flags are enabled", not missing_flags, f"Missing flags: {', '.join(missing_flags) or 'none'}."),
        _readiness_check("no_live_money_routes", "No payment/payout/wallet routes exist", not money_route_findings, "No Mutual Aid payment, payout, or wallet routes may be registered."),
    ]
    blockers = [check for check in checks if not check["passed"]]
    return {
        "ok": True,
        "ready": not blockers,
        "status": "go" if not blockers else "no-go",
        "next_required_action": "Maintain pilot-safe controls and collect final operator signoff." if not blockers else blockers[0]["detail"],
        "blockers": blockers,
        "checks": checks,
        "phase8_readiness": phase8,
        "guardrails": ["No money movement", "No payment processors", "No payout execution", "No wallet balances", "No distributions before activation"],
    }


@router.get("/admin/pilot-launch-lock/verification")
def pilot_launch_lock_verification(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    return _launch_lock_response(db)


def _pilot_runbook_response(db):
    flags = mutual_aid_feature_flags()
    phase8 = pilot_readiness_verification(db=db)
    launch_lock = _launch_lock_response(db)
    missing_flags = [key for key in REQUIRED_RUNBOOK_FLAGS if not flags.get(key)]
    required_docs = [
        "SIMBA_MUTUAL_AID_SOCIETY_BINDER.md",
        "SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md",
        "SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md",
        "SIMBA_PILOT_READINESS_REPORT.md",
    ]
    checklist = [
        _readiness_check("readiness_verified", "Verify Phase 8 readiness", phase8["ready"], "Confirm Phase 8 readiness still passes."),
        _readiness_check("launch_lock_verified", "Verify Phase 9 launch lock", launch_lock["ready"], "Confirm Phase 9 launch lock still passes."),
        _readiness_check("payments_disabled", "Confirm payments remain disabled", not flags["ENABLE_MUTUAL_AID_PAYMENTS"], "ENABLE_MUTUAL_AID_PAYMENTS must remain false."),
        _readiness_check("no_money_routes", "Confirm no payment/payout/wallet routes exist", not phase8["money_route_findings"], "Registered Mutual Aid routes must remain read-only for money movement."),
        _readiness_check("export_only", "Use print/export view only", True, "Operators may print from the browser; no downloads, file storage, persistence, or signoff writes are performed."),
    ]
    blockers = [check for check in checklist if not check["passed"]]
    if missing_flags:
        blockers.append(_readiness_check("required_flags_present", "Required runbook flags are enabled", False, f"Missing flags: {', '.join(missing_flags)}."))
    ready = not blockers
    return {
        "ok": True,
        "phase": "Phase 10 pilot runbook",
        "ready": ready,
        "status": "go" if ready else "no-go",
        "go_no_go_result": "GO" if ready else "NO-GO",
        "pilot_status": "Read-only pilot operations only",
        "phase8_readiness": {"ready": phase8["ready"], "status": "pass" if phase8["ready"] else "fail", "checks": phase8["checks"]},
        "phase9_launch_lock": {"ready": launch_lock["ready"], "status": launch_lock["status"], "checks": launch_lock["checks"]},
        "blockers": blockers + launch_lock["blockers"],
        "operator_checklist": checklist,
        "required_roles": sorted(REQUIRED_LAUNCH_LOCK_ROLES),
        "required_flags": list(REQUIRED_RUNBOOK_FLAGS) + ["ENABLE_MUTUAL_AID_PAYMENTS=false"],
        "required_docs_policies": required_docs,
        "guardrails": [
            "No money movement",
            "No payment processors connected",
            "No payout execution",
            "No wallet balances",
            "No STAR, Black Dollar, ownership, partner reimbursement, payment, payout, or wallet integrations",
            "No downloads, file storage, persistence, or signoff writes from this export view",
        ],
    }


@router.get("/admin/pilot-runbook/verification")
def pilot_runbook_verification(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    return _pilot_runbook_response(db)


def _pilot_smoke_tests_response(db):
    flags = mutual_aid_feature_flags()
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    phase8 = pilot_readiness_verification(db=db)
    launch_lock = _launch_lock_response(db)
    runbook = _pilot_runbook_response(db)
    money_route_findings = _live_money_route_findings()
    missing_flags = [key for key in REQUIRED_SMOKE_TEST_FLAGS if not flags.get(key)]
    checks = [
        _readiness_check("request_intake_flag", "Request intake flag enabled", flags["MUTUAL_AID_REQUESTS_ENABLED"] and flags["ENABLE_MUTUAL_AID_REQUEST_INTAKE"], "Request intake must be enabled for the pilot smoke test."),
        _readiness_check("review_flag", "Review flag enabled", flags["MUTUAL_AID_REVIEW_ENABLED"] and flags["ENABLE_MUTUAL_AID_REVIEW_WORKFLOW"], "Review workflow must be enabled for the pilot smoke test."),
        _readiness_check("decision_flag", "Decision flag enabled", flags["MUTUAL_AID_DECISIONS_ENABLED"], "Decision workflow must be enabled for the pilot smoke test."),
        _readiness_check("financial_controls_flag", "Financial controls flag enabled", flags["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"], "Financial controls must be enabled for the pilot smoke test."),
        _readiness_check("disbursement_tracking_flag", "Disbursement tracking flag enabled", flags["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"], "Disbursement tracking must be enabled as record-only tracking."),
        _readiness_check("notifications_flag", "Notifications flag enabled", flags["MUTUAL_AID_NOTIFICATIONS_ENABLED"], "Internal recorded-only notifications must be enabled."),
        _readiness_check("appeals_flag", "Appeals flag enabled", flags["MUTUAL_AID_APPEALS_ENABLED"], "Appeals workflow must be enabled for the pilot smoke test."),
        _readiness_check("hardening_flag", "Hardening flag enabled", flags["MUTUAL_AID_PILOT_HARDENING_ENABLED"], "Pilot hardening must be enabled."),
        _readiness_check("launch_lock_flag", "Launch lock flag enabled", flags["MUTUAL_AID_PILOT_LAUNCH_LOCK_ENABLED"], "Pilot launch lock must be enabled."),
        _readiness_check("runbook_flag", "Runbook flag enabled", flags["MUTUAL_AID_PILOT_RUNBOOK_ENABLED"], "Pilot runbook must be enabled."),
        _readiness_check("smoke_tests_flag", "Smoke tests flag enabled", flags["MUTUAL_AID_PILOT_SMOKE_TESTS_ENABLED"], "Pilot smoke tests must be explicitly enabled."),
        _readiness_check("payments_disabled", "Payments disabled", not flags["ENABLE_MUTUAL_AID_PAYMENTS"], "ENABLE_MUTUAL_AID_PAYMENTS must remain false."),
        _readiness_check("no_money_routes", "No payment/payout/wallet routes", not money_route_findings, "No Mutual Aid payment, payout, or wallet routes may be registered."),
        _readiness_check("fund_status_building", "Fund status is Building Toward Activation", bool(fund and fund.status == MUTUAL_AID_BUILDING_STATUS), f"Expected {MUTUAL_AID_BUILDING_STATUS}."),
        _readiness_check("activation_threshold_20000", "Activation threshold is 20000", bool(fund and fund.activation_threshold == MUTUAL_AID_ACTIVATION_THRESHOLD), f"Expected {MUTUAL_AID_ACTIVATION_THRESHOLD}."),
        _readiness_check("phase8_readiness_passes", "Phase 8 readiness passes", phase8["ready"], "Phase 8 readiness must pass."),
        _readiness_check("phase9_launch_lock_passes", "Phase 9 launch lock passes", launch_lock["ready"], "Phase 9 launch lock must pass."),
        _readiness_check("phase10_runbook_passes", "Phase 10 runbook passes", runbook["ready"], "Phase 10 runbook must pass."),
    ]
    blockers = [check for check in checks if not check["passed"]]
    if missing_flags:
        blockers.append(_readiness_check("required_phase_flag_missing", "Required phase flag missing", False, f"Missing flags: {', '.join(missing_flags)}."))
    passed = not blockers
    return {
        "ok": True,
        "phase": "Phase 11 pilot operations smoke tests",
        "read_only": True,
        "persisted": False,
        "status": "pass" if passed else "fail",
        "passed": passed,
        "blockers": blockers,
        "next_action": "Proceed with read-only pilot operations monitoring; do not enable money movement." if passed else blockers[0]["detail"],
        "pilot_safe_warnings": [
            "No live submissions are created by this smoke test.",
            "No money movement, payment processing, payout execution, or wallet balances are available.",
            "No STAR, Black Dollar, ownership, partner reimbursement, payment, payout, or wallet integrations are checked in.",
        ],
        "no_persistence_warning": "This endpoint performs read-only verification only and does not persist smoke test results, signoff, exports, submissions, disbursements, or notifications.",
        "checks": checks,
        "money_route_findings": money_route_findings,
        "mutual_aid_routes": [f"/mutual-aid{path}" for path in _mutual_aid_route_paths()],
        "fund_status": fund.status if fund else None,
        "activation_threshold": fund.activation_threshold if fund else None,
        "required_flags": list(REQUIRED_SMOKE_TEST_FLAGS) + ["ENABLE_MUTUAL_AID_PAYMENTS=false"],
    }


@router.get("/admin/pilot-smoke-tests/verification")
def pilot_smoke_tests_verification(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    return _pilot_smoke_tests_response(db)


def _pct(numerator, denominator):
    return round((numerator / denominator) * 100, 2) if denominator else 0


def _avg_hours(deltas):
    values = [delta.total_seconds() / 3600 for delta in deltas if delta]
    return round(sum(values) / len(values), 2) if values else 0


def _count_by(rows, attr, allowed=None):
    keys = list(allowed or [])
    counts = {key: 0 for key in keys}
    for row in rows:
        key = (getattr(row, attr, None) or "unknown").strip().lower()
        counts[key] = counts.get(key, 0) + 1
    return counts


def _analytics_allowed(db, user):
    if user_has_permission(db, user, "mutual_aid:read_analytics"):
        return True
    if (user.role or "").strip().lower() == "governance":
        return True
    return db.query(MutualAidCommitteeMember).filter(
        MutualAidCommitteeMember.user_id == user.id,
        MutualAidCommitteeMember.status == "active",
        MutualAidCommitteeMember.role.in_(["governance", "treasurer"]),
    ).first() is not None


def _require_analytics_access(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if not _analytics_allowed(db, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


def _mutual_aid_analytics_response(db):
    requests = db.query(MutualAidRequest).all()
    decisions = db.query(MutualAidDecision).all()
    appeals = db.query(MutualAidAppeal).all()
    notifications = db.query(MutualAidNotification).all()
    audits = db.query(MutualAidAuditLog).all()
    disbursements = db.query(MutualAidDisbursement).all()
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    budgets = db.query(MutualAidCategoryBudget).filter(MutualAidCategoryBudget.fund_id == fund.id).all() if fund else []
    status_counts = _count_by(requests, "status", ["draft", "submitted", "under_review", "more_info_requested", "approved", "partially_approved", "not_approved", "closed"])
    approval_count = status_counts.get("approved", 0) + status_counts.get("partially_approved", 0)
    decision_deltas = []
    review_deltas = []
    for req in requests:
        first_review = db.query(MutualAidRequestStatusHistory).filter(MutualAidRequestStatusHistory.request_id == req.id, MutualAidRequestStatusHistory.to_status == "under_review").order_by(MutualAidRequestStatusHistory.created_at.asc()).first()
        first_decision = db.query(MutualAidDecision).filter(MutualAidDecision.request_id == req.id).order_by(MutualAidDecision.created_at.asc()).first()
        if req.submitted_at and first_review and first_review.created_at:
            review_deltas.append(first_review.created_at - req.submitted_at)
        if req.submitted_at and first_decision and first_decision.created_at:
            decision_deltas.append(first_decision.created_at - req.submitted_at)
    disbursement_by_status = _count_by(disbursements, "status", DISBURSEMENT_STATUSES)
    disbursement_amounts = {status_key: sum(row.amount for row in disbursements if row.status == status_key) for status_key in disbursement_by_status}
    category_budget_utilization = []
    for budget in budgets:
        spent = sum(d.amount for d in disbursements if d.status not in {"cancelled", "reversed", "failed"} and db.query(MutualAidRequest).filter(MutualAidRequest.id == d.request_id, MutualAidRequest.category == budget.category).first())
        category_budget_utilization.append({"category": budget.category, "budget_amount": budget.budget_amount, "reserved_amount": budget.reserved_amount, "tracked_amount": spent, "utilization_rate": _pct(budget.reserved_amount + spent, budget.budget_amount), "currency": budget.currency})
    reserve_floor = (fund.current_balance * fund.reserve_percent // 100) if fund else 0
    reserved = sum(row.amount for row in disbursements if row.status in {"pending", "scheduled", "needs_receipt"})
    activation_percent = _pct(fund.current_balance if fund else 0, fund.activation_threshold if fund else MUTUAL_AID_ACTIVATION_THRESHOLD)
    report = {
        "ok": True, "read_only": True, "persisted": False,
        "feature_enabled": settings.MUTUAL_AID_ANALYTICS_ENABLED,
        "guardrails": ["No payment processors", "No money movement", "No payout execution", "No wallet balances", "No reimbursement logic", "No STAR, Black Dollar, ownership, or partner reimbursement integration"],
        "totals": {"total_requests": len(requests), "draft_requests": status_counts.get("draft", 0), "submitted_requests": status_counts.get("submitted", 0), "under_review": status_counts.get("under_review", 0), "more_info_requests": status_counts.get("more_info_requested", 0), "approved": status_counts.get("approved", 0), "partially_approved": status_counts.get("partially_approved", 0), "denied": status_counts.get("not_approved", 0), "appealed": len(appeals), "closed": status_counts.get("closed", 0)},
        "timing": {"average_review_time_hours": _avg_hours(review_deltas), "average_decision_time_hours": _avg_hours(decision_deltas)},
        "volume": {"by_category": _count_by(requests, "category", CATEGORIES), "by_urgency": _count_by(requests, "urgency", URGENCIES), "by_status": status_counts},
        "rates": {"approval_rate": _pct(approval_count, len(decisions) or len(requests)), "appeal_rate": _pct(len(appeals), len(decisions) or len(requests))},
        "notifications": {"total": len(notifications), "by_event_type": _count_by(notifications, "event_type"), "by_delivery_status": _count_by(notifications, "delivery_status")},
        "audit_activity": {"total": len(audits), "by_action": _count_by(audits, "action")},
        "disbursements": {"total_records": len(disbursements), "by_status": disbursement_by_status, "amounts_by_status": disbursement_amounts},
        "budgets": {"category_budget_utilization": category_budget_utilization, "reserve_utilization": {"current_balance": fund.current_balance if fund else 0, "reserve_percent": fund.reserve_percent if fund else 0, "reserve_floor": reserve_floor, "reserved_tracking_total": reserved, "utilization_rate": _pct(reserved, reserve_floor), "currency": fund.currency if fund else "USD"}},
        "activation": {"status": fund.status if fund else MUTUAL_AID_BUILDING_STATUS, "building_toward_activation": bool(fund and fund.status == MUTUAL_AID_BUILDING_STATUS), "current_progress": fund.current_balance if fund else 0, "activation_threshold": fund.activation_threshold if fund else MUTUAL_AID_ACTIVATION_THRESHOLD, "progress_percent": activation_percent},
        "executive_kpis": [
            {"label": "Total Requests", "value": len(requests), "detail": "All Mutual Aid requests in the read-only analytics window."},
            {"label": "Approval Rate", "value": f"{_pct(approval_count, len(decisions) or len(requests))}%", "detail": "Approved or partially approved share."},
            {"label": "Appeal Rate", "value": f"{_pct(len(appeals), len(decisions) or len(requests))}%", "detail": "Appeals compared with decisions or request volume."},
            {"label": "Activation Progress", "value": f"{activation_percent}%", "detail": "Building Toward Activation threshold progress."},
            {"label": "Notifications", "value": len(notifications), "detail": "Recorded-only notification events."},
            {"label": "Audit Events", "value": len(audits), "detail": "Governance audit activity records."},
        ],
        "reporting": {"printable_executive_report": True, "csv_export_scaffold": True, "pdf_export_scaffold": True, "file_storage": False, "persistence": False, "scheduled_reports": False},
    }
    return report


@router.get("/admin/analytics/executive")
def executive_analytics(current_user: User = Depends(_require_analytics_access), db: Session = Depends(get_db)):
    if not settings.MUTUAL_AID_ANALYTICS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid analytics are not enabled")
    return _mutual_aid_analytics_response(db)


def _ensure_enabled():
    if not settings.MUTUAL_AID_REQUESTS_ENABLED or settings.ENABLE_MUTUAL_AID_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid request intake is not enabled")


def _ensure_review_enabled():
    _ensure_enabled()
    if not settings.MUTUAL_AID_REVIEW_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid review workflow is not enabled")

def _ensure_decisions_enabled():
    _ensure_review_enabled()
    if not settings.MUTUAL_AID_DECISIONS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid decision workflow is not enabled")

def _ensure_appeals_enabled():
    _ensure_decisions_enabled()
    if not settings.MUTUAL_AID_APPEALS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid appeals workflow is not enabled")


def _fund(db):
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    if not fund:
        raise HTTPException(status_code=503, detail="Mutual Aid fund is not initialized")
    return fund


def _validate_payload(payload: RequestPayload):
    category = payload.category.strip().lower()
    urgency = payload.urgency.strip().lower()
    support = payload.preferred_support_method.strip().lower()
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Unsupported Mutual Aid request category")
    if urgency not in URGENCIES:
        raise HTTPException(status_code=422, detail="Unsupported Mutual Aid urgency")
    if support not in SUPPORT_METHODS:
        raise HTTPException(status_code=422, detail="Unsupported preferred support method")
    if not payload.policy_consent:
        raise HTTPException(status_code=422, detail="Policy consent is required")
    return category, urgency, support


def _serialize_user(user: User | None):
    if not user:
        return None
    return {"id": user.id, "email": user.email, "role": user.role}

def _serialize(req: MutualAidRequest):
    return {
        "id": req.id,
        "category": req.category,
        "urgency": req.urgency,
        "requested_amount": req.amount_requested,
        "currency": req.currency,
        "status": req.status,
        "explanation": req.narrative,
        "preferred_support_method": req.preferred_support_method,
        "policy_consent": req.policy_consent,
        "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }


def _audit(db, actor_id, entity_id, action, before=None, after=None, entity_type="mutual_aid_request"):
    db.add(MutualAidAuditLog(actor_user_id=actor_id, entity_type=entity_type, entity_id=entity_id, action=action, before=before or {}, after=after or {}))


def _serialize_history(row: MutualAidRequestStatusHistory):
    return {"id": row.id, "from_status": row.from_status, "to_status": row.to_status, "changed_by_user_id": row.changed_by_user_id, "reason": row.reason, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_review(row: MutualAidReview):
    return {"id": row.id, "request_id": row.request_id, "reviewer_user_id": row.reviewer_user_id, "status": row.status, "notes": row.notes, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_conflict(row: MutualAidConflictDisclosure):
    return {"id": row.id, "request_id": row.request_id, "committee_member_id": row.committee_member_id, "disclosure": row.disclosure, "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_decision(row: MutualAidDecision):
    return {"id": row.id, "request_id": row.request_id, "decision": row.decision, "decided_by_user_id": row.decided_by_user_id, "approved_amount": row.amount_approved, "reason_code": row.reason_code, "notes": row.rationale, "appeal_eligible": row.appeal_eligible, "appeal_deadline": row.appeal_deadline.isoformat() if row.appeal_deadline else None, "appeal_instructions": row.appeal_instructions, "created_at": row.created_at.isoformat() if row.created_at else None}

def _serialize_appeal(row: MutualAidAppeal):
    return {"id": row.id, "request_id": row.request_id, "decision_id": row.decision_id, "appellant_user_id": row.appellant_user_id, "status": row.status, "reason": row.reason, "explanation": row.explanation, "reviewed_by_user_id": row.reviewed_by_user_id, "review_notes": row.review_notes, "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None, "closed_at": row.closed_at.isoformat() if row.closed_at else None, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}

def _serialize_notification(row: MutualAidNotification):
    return {"id": row.id, "request_id": row.request_id, "disbursement_id": row.disbursement_id, "recipient_user_id": row.recipient_user_id, "actor_user_id": row.actor_user_id, "audience": row.audience, "event_type": row.event_type, "title": row.title, "message": row.message, "delivery_status": row.delivery_status, "channels": row.channels, "payload": row.payload, "created_at": row.created_at.isoformat() if row.created_at else None}

def _request_notifications(db, request_id):
    return db.query(MutualAidNotification).filter(MutualAidNotification.request_id == request_id).order_by(MutualAidNotification.created_at.desc()).all()

def _request_appeals(db, request_id):
    return db.query(MutualAidAppeal).filter(MutualAidAppeal.request_id == request_id).order_by(MutualAidAppeal.created_at.desc()).all()

def _latest_not_approved_decision(db, request_id):
    return db.query(MutualAidDecision).filter(MutualAidDecision.request_id == request_id, MutualAidDecision.decision == "not_approved").order_by(MutualAidDecision.created_at.desc()).first()

def _is_admin(db, user):
    return user_has_permission(db, user, "mutual_aid:read_requests_admin")

def _assigned_review(db, request_id, user_id):
    return db.query(MutualAidReview).filter(MutualAidReview.request_id == request_id, MutualAidReview.reviewer_user_id == user_id).order_by(MutualAidReview.created_at.desc()).first()

def _ensure_reviewer_access(db, req, current_user):
    if _is_admin(db, current_user):
        return
    if not _assigned_review(db, req.id, current_user.id):
        raise HTTPException(status_code=404, detail="Request not found")

def _ensure_financial_controls_enabled():
    _ensure_decisions_enabled()
    if not settings.MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED or settings.ENABLE_MUTUAL_AID_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid financial controls are not enabled")

def _ensure_disbursement_tracking_enabled():
    _ensure_financial_controls_enabled()
    if not settings.MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mutual Aid disbursement tracking is not enabled")

def _latest_approval(db, request_id):
    return db.query(MutualAidDecision).filter(MutualAidDecision.request_id == request_id, MutualAidDecision.decision.in_(["approve", "partial_approve"])).order_by(MutualAidDecision.created_at.desc()).first()

def _disbursed_total(db, request_id):
    rows = db.query(MutualAidDisbursement).filter(MutualAidDisbursement.request_id == request_id, MutualAidDisbursement.status.notin_(["cancelled", "reversed", "failed"])).all()
    return sum(row.amount for row in rows)

def _serialize_disbursement(row: MutualAidDisbursement):
    return {"id": row.id, "request_id": row.request_id, "recipient_user_id": row.recipient_user_id, "amount": row.amount, "currency": row.currency, "status": row.status, "receipt_required": row.receipt_required, "scheduled_for": row.scheduled_for.isoformat() if row.scheduled_for else None, "notes": row.notes, "created_by_user_id": row.created_by_user_id, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}

def _fund_balance_read_model(db, fund):
    active = db.query(MutualAidDisbursement).join(MutualAidRequest, MutualAidRequest.id == MutualAidDisbursement.request_id).filter(MutualAidRequest.fund_id == fund.id, MutualAidDisbursement.status.in_(["pending", "scheduled", "needs_receipt"])).all()
    paid = db.query(MutualAidDisbursement).join(MutualAidRequest, MutualAidRequest.id == MutualAidDisbursement.request_id).filter(MutualAidRequest.fund_id == fund.id, MutualAidDisbursement.status.in_(["paid", "closed"])).all()
    reserved = sum(row.amount for row in active)
    paid_total = sum(row.amount for row in paid)
    reserve_floor = fund.current_balance * fund.reserve_percent // 100
    return {"fund_id": fund.id, "current_balance": fund.current_balance, "reserved_balance": reserved, "paid_total": paid_total, "reserve_percent": fund.reserve_percent, "reserve_floor": reserve_floor, "available_for_disbursement": max(fund.current_balance - reserve_floor - reserved, 0), "approval_threshold": fund.approval_threshold, "currency": fund.currency}

def _has_open_conflict(db, request_id, reviewer_id):
    review = _assigned_review(db, request_id, reviewer_id)
    if not review:
        return False
    return db.query(MutualAidConflictDisclosure).filter(MutualAidConflictDisclosure.request_id == request_id, MutualAidConflictDisclosure.committee_member_id == review.id, MutualAidConflictDisclosure.status == "open").first() is not None


@router.post("/requests/draft")
def create_draft(payload: RequestPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    category, urgency, support = _validate_payload(payload)
    req = MutualAidRequest(fund_id=_fund(db).id, requester_user_id=current_user.id, category=category, urgency=urgency, amount_requested=payload.requested_amount, narrative=payload.explanation.strip(), preferred_support_method=support, policy_consent=True, status="draft")
    db.add(req); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=None, to_status="draft", changed_by_user_id=current_user.id, reason="member draft saved"))
    _audit(db, current_user.id, req.id, "draft_saved", after=_serialize(req))
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}


@router.post("/requests/{request_id}/submit")
def submit_request(request_id: int, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "draft": raise HTTPException(status_code=409, detail="Only draft requests can be submitted")
    before = _serialize(req); req.status = "submitted"; req.submitted_at = datetime.utcnow()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status="draft", to_status="submitted", changed_by_user_id=current_user.id, reason="member submitted request"))
    _audit(db, current_user.id, req.id, "submitted", before=before, after=_serialize(req)); _audit(db, current_user.id, req.id, "status_changed", before={"status":"draft"}, after={"status":"submitted"})
    record_mutual_aid_notification(db, event_type="request_submitted", request_id=req.id, recipient_user_id=current_user.id, actor_user_id=current_user.id, payload={"status": "submitted"})
    record_mutual_aid_notification(db, event_type="admin_request_submitted", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"requester_user_id": current_user.id, "status": "submitted"})
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}


@router.get("/requests/{request_id}")
def get_request(request_id: int, current_user: User = Depends(require_permission("mutual_aid:read_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_user_id != current_user.id and not user_has_permission(db, current_user, "mutual_aid:read_requests_admin"):
        raise HTTPException(status_code=404, detail="Request not found")
    notifications = db.query(MutualAidNotification).filter(MutualAidNotification.request_id == req.id, MutualAidNotification.recipient_user_id == current_user.id).order_by(MutualAidNotification.created_at.desc()).all()
    appeals = _request_appeals(db, req.id)
    return {"ok": True, "request": _serialize(req), "appeals": [_serialize_appeal(a) for a in appeals], "notifications": [_serialize_notification(n) for n in notifications]}


@router.get("/admin/requests")
def admin_requests(current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    return {"ok": True, "requests": [_serialize(r) for r in db.query(MutualAidRequest).order_by(MutualAidRequest.created_at.desc()).all()]}



@router.get("/admin/requests/{request_id}")
def admin_request_detail(request_id: int, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    reviews = db.query(MutualAidReview).filter(MutualAidReview.request_id == req.id).order_by(MutualAidReview.created_at.desc()).all()
    history = db.query(MutualAidRequestStatusHistory).filter(MutualAidRequestStatusHistory.request_id == req.id).order_by(MutualAidRequestStatusHistory.created_at.desc()).all()
    conflicts = db.query(MutualAidConflictDisclosure).filter(MutualAidConflictDisclosure.request_id == req.id).order_by(MutualAidConflictDisclosure.created_at.desc()).all()
    decisions = db.query(MutualAidDecision).filter(MutualAidDecision.request_id == req.id).order_by(MutualAidDecision.created_at.desc()).all()
    requester = db.query(User).filter(User.id == req.requester_user_id).first() if req.requester_user_id else None
    notifications = _request_notifications(db, req.id)
    appeals = _request_appeals(db, req.id)
    return {"ok": True, "request": _serialize(req), "requester": _serialize_user(requester), "reviews": [_serialize_review(r) for r in reviews], "status_history": [_serialize_history(h) for h in history], "conflicts": [_serialize_conflict(c) for c in conflicts], "decisions": [_serialize_decision(d) for d in decisions], "appeals": [_serialize_appeal(a) for a in appeals], "notifications": [_serialize_notification(n) for n in notifications], "decision_reason_codes": sorted(DECISION_REASON_CODES), "appeal_statuses": sorted(APPEAL_STATUSES)}


@router.post("/admin/requests/{request_id}/decision")
def record_decision(request_id: int, payload: DecisionPayload, current_user: User = Depends(require_permission("mutual_aid:decide_requests")), db: Session = Depends(get_db)):
    _ensure_decisions_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    decision_value = payload.decision.strip().lower()
    reason_code = payload.reason_code.strip().lower()
    if decision_value not in DECISIONS: raise HTTPException(status_code=422, detail="Unsupported Mutual Aid decision")
    if reason_code not in DECISION_REASON_CODES: raise HTTPException(status_code=422, detail="Unsupported Mutual Aid decision reason code")
    if decision_value in {"approve", "partial_approve"} and payload.approved_amount <= 0: raise HTTPException(status_code=422, detail="Approved decisions require an approved amount")
    if decision_value in {"not_approved", "close"} and payload.approved_amount != 0: raise HTTPException(status_code=422, detail="Non-approval decisions cannot record an approved amount")
    if _has_open_conflict(db, req.id, current_user.id): raise HTTPException(status_code=409, detail="Conflicted reviewers cannot decide")
    before = _serialize(req)
    next_status = DECISION_STATUS[decision_value]
    decision = MutualAidDecision(request_id=req.id, decision=decision_value, decided_by_user_id=current_user.id, amount_approved=payload.approved_amount, reason_code=reason_code, rationale=payload.notes.strip(), appeal_eligible=payload.appeal_eligible, appeal_deadline=payload.appeal_deadline, appeal_instructions=payload.appeal_instructions.strip())
    req.status = next_status
    db.add(decision); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=next_status, changed_by_user_id=current_user.id, reason=f"decision:{decision_value}:{reason_code}"))
    _audit(db, current_user.id, req.id, "decision_recorded", before=before, after={"request": _serialize(req), "decision": _serialize_decision(decision)})
    record_mutual_aid_notification(db, event_type="decision_recorded", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"decision": decision_value, "status": next_status, "appeal_eligible": payload.appeal_eligible})
    record_mutual_aid_notification(db, event_type="admin_decision_recorded", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"decision": decision_value, "status": next_status})
    if payload.appeal_eligible:
        record_mutual_aid_notification(db, event_type="appeal_window_reminder", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"appeal_deadline": payload.appeal_deadline.isoformat() if payload.appeal_deadline else None})
    _audit(db, current_user.id, req.id, "status_changed", before={"status": before["status"]}, after={"status": next_status})
    db.commit(); db.refresh(decision); db.refresh(req)
    return {"ok": True, "request": _serialize(req), "decision": _serialize_decision(decision)}

@router.post("/admin/requests/{request_id}/assign-reviewer")
def assign_reviewer(request_id: int, payload: AssignReviewerPayload, current_user: User = Depends(require_permission("mutual_aid:read_requests_admin")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    reviewer = db.query(User).filter(User.id == payload.reviewer_user_id).first()
    if not req or not reviewer: raise HTTPException(status_code=404, detail="Request not found")
    review = MutualAidReview(request_id=req.id, reviewer_user_id=reviewer.id, status="assigned", notes="")
    before = {"status": req.status}; req.status = "under_review"
    db.add(review); db.flush()
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=req.status, changed_by_user_id=current_user.id, reason=f"reviewer assigned: {reviewer.id}"))
    _audit(db, current_user.id, req.id, "reviewer_assigned", before=before, after={"status": req.status, "reviewer_user_id": reviewer.id, "review_id": review.id})
    db.commit(); db.refresh(review)
    return {"ok": True, "review": _serialize_review(review), "request": _serialize(req)}

@router.post("/admin/requests/{request_id}/recommendation")
def reviewer_recommendation(request_id: int, payload: RecommendationPayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    if _has_open_conflict(db, req.id, current_user.id): raise HTTPException(status_code=409, detail="Conflicted reviewers cannot recommend")
    review = _assigned_review(db, req.id, current_user.id) or MutualAidReview(request_id=req.id, reviewer_user_id=current_user.id)
    before = _serialize_review(review) if review.id else {}
    review.status = f"recommended_{payload.recommendation.strip().lower()}"; review.notes = payload.notes.strip()
    db.add(review); db.flush()
    _audit(db, current_user.id, req.id, "recommendation_recorded", before=before, after=_serialize_review(review))
    db.commit(); db.refresh(review)
    return {"ok": True, "review": _serialize_review(review)}

@router.post("/admin/requests/{request_id}/request-more-info")
def request_more_info(request_id: int, payload: MoreInfoPayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    before = {"status": req.status}; req.status = "more_info_requested"
    db.add(MutualAidRequestStatusHistory(request_id=req.id, from_status=before["status"], to_status=req.status, changed_by_user_id=current_user.id, reason=payload.message.strip()))
    _audit(db, current_user.id, req.id, "more_info_requested", before=before, after={"status": req.status, "message": payload.message.strip()})
    record_mutual_aid_notification(db, event_type="more_information_requested", request_id=req.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": req.status, "message": payload.message.strip()})
    record_mutual_aid_notification(db, event_type="admin_more_information_requested", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": req.status})
    db.commit(); db.refresh(req)
    return {"ok": True, "request": _serialize(req)}

@router.post("/admin/requests/{request_id}/conflict-disclosure")
def disclose_conflict(request_id: int, payload: ConflictDisclosurePayload, current_user: User = Depends(require_permission("mutual_aid:review_requests")), db: Session = Depends(get_db)):
    _ensure_review_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    _ensure_reviewer_access(db, req, current_user)
    review = _assigned_review(db, req.id, current_user.id)
    if not review: raise HTTPException(status_code=404, detail="Assigned review not found")
    conflict = MutualAidConflictDisclosure(request_id=req.id, committee_member_id=review.id, disclosure=payload.disclosure.strip(), status="open")
    db.add(conflict); db.flush()
    _audit(db, current_user.id, req.id, "conflict_disclosed", after=_serialize_conflict(conflict))
    db.commit(); db.refresh(conflict)
    return {"ok": True, "conflict": _serialize_conflict(conflict)}

@router.post("/requests/{request_id}/appeals")
def submit_appeal(request_id: int, payload: AppealPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_appeals_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "not_approved":
        raise HTTPException(status_code=409, detail="Only not-approved requests can be appealed")
    decision = _latest_not_approved_decision(db, req.id)
    if not decision or not decision.appeal_eligible:
        raise HTTPException(status_code=409, detail="This request is not appeal eligible")
    if decision.appeal_deadline and datetime.utcnow() > decision.appeal_deadline:
        raise HTTPException(status_code=409, detail="The appeal deadline has passed")
    existing = db.query(MutualAidAppeal).filter(MutualAidAppeal.request_id == req.id, MutualAidAppeal.status.in_(["submitted", "under_review", "more_info_requested"])).first()
    if existing:
        raise HTTPException(status_code=409, detail="An open appeal already exists for this request")
    appeal = MutualAidAppeal(request_id=req.id, decision_id=decision.id, appellant_user_id=current_user.id, status="submitted", reason=payload.reason.strip(), explanation=payload.explanation.strip())
    db.add(appeal); db.flush()
    _audit(db, current_user.id, appeal.id, "appeal_submitted", after=_serialize_appeal(appeal), entity_type="mutual_aid_appeal")
    _audit(db, current_user.id, req.id, "appeal_submitted", after={"appeal": _serialize_appeal(appeal)})
    record_mutual_aid_notification(db, event_type="appeal_submitted", request_id=req.id, recipient_user_id=current_user.id, actor_user_id=current_user.id, payload={"appeal_id": appeal.id, "status": appeal.status})
    record_mutual_aid_notification(db, event_type="admin_appeal_submitted", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"appeal_id": appeal.id, "status": appeal.status})
    db.commit(); db.refresh(appeal)
    return {"ok": True, "appeal": _serialize_appeal(appeal)}

@router.post("/admin/appeals/{appeal_id}/review")
def review_appeal(appeal_id: int, payload: AppealReviewPayload, current_user: User = Depends(require_permission("mutual_aid:decide_requests")), db: Session = Depends(get_db)):
    _ensure_appeals_enabled()
    appeal = db.query(MutualAidAppeal).filter(MutualAidAppeal.id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in APPEAL_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported appeal status")
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == appeal.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    before = _serialize_appeal(appeal)
    appeal.status = normalized_status
    appeal.review_notes = payload.notes.strip()
    appeal.reviewed_by_user_id = current_user.id
    appeal.reviewed_at = datetime.utcnow()
    if normalized_status in {"approved", "denied", "closed"}:
        appeal.closed_at = appeal.reviewed_at
    _audit(db, current_user.id, appeal.id, "appeal_reviewed", before=before, after=_serialize_appeal(appeal), entity_type="mutual_aid_appeal")
    _audit(db, current_user.id, req.id, "appeal_reviewed", before={"appeal": before}, after={"appeal": _serialize_appeal(appeal)})
    record_mutual_aid_notification(db, event_type="appeal_status_changed", request_id=req.id, recipient_user_id=appeal.appellant_user_id, actor_user_id=current_user.id, payload={"appeal_id": appeal.id, "status": appeal.status})
    record_mutual_aid_notification(db, event_type="admin_appeal_status_changed", request_id=req.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"appeal_id": appeal.id, "status": appeal.status})
    db.commit(); db.refresh(appeal)
    return {"ok": True, "appeal": _serialize_appeal(appeal)}

@router.post("/requests/{request_id}/documents/metadata")
def document_metadata(request_id: int, payload: DocumentMetadataPayload, current_user: User = Depends(require_permission("mutual_aid:create_request_self")), db: Session = Depends(get_db)):
    _ensure_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id, MutualAidRequest.requester_user_id == current_user.id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    doc = MutualAidRequestDocument(request_id=req.id, document_type=payload.document_type.strip() or "supporting", filename=payload.filename.strip(), content_type=payload.content_type.strip(), file_size=payload.file_size, storage_key=payload.storage_key.strip(), status="metadata_only")
    db.add(doc); db.flush()
    _audit(db, current_user.id, req.id, "document_metadata_added", after={"document_id": doc.id, "filename": doc.filename, "content_type": doc.content_type, "file_size": doc.file_size})
    db.commit()
    return {"ok": True, "document": {"id": doc.id, "filename": doc.filename, "status": doc.status}}


@router.get("/admin/financial-controls")
def financial_controls(current_user: User = Depends(require_permission("mutual_aid:read_financial_controls")), db: Session = Depends(get_db)):
    _ensure_financial_controls_enabled()
    fund = _fund(db)
    budgets = db.query(MutualAidCategoryBudget).filter(MutualAidCategoryBudget.fund_id == fund.id).order_by(MutualAidCategoryBudget.category.asc()).all()
    reports = db.query(MutualAidReconciliationReport).filter(MutualAidReconciliationReport.fund_id == fund.id).order_by(MutualAidReconciliationReport.created_at.desc()).all()
    return {"ok": True, "balance": _fund_balance_read_model(db, fund), "category_budgets": [{"id": b.id, "category": b.category, "budget_amount": b.budget_amount, "reserved_amount": b.reserved_amount, "currency": b.currency} for b in budgets], "reconciliation_reports": [{"id": r.id, "status": r.status, "totals": r.totals, "created_at": r.created_at.isoformat() if r.created_at else None} for r in reports]}

@router.get("/admin/disbursements")
def list_disbursements(current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    rows = db.query(MutualAidDisbursement).order_by(MutualAidDisbursement.created_at.desc()).all()
    return {"ok": True, "statuses": sorted(DISBURSEMENT_STATUSES), "disbursements": [_serialize_disbursement(row) for row in rows]}

@router.post("/admin/requests/{request_id}/disbursements")
def create_disbursement(request_id: int, payload: DisbursementPayload, current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in {"approved", "partially_approved"}: raise HTTPException(status_code=409, detail="Only approved requests can receive disbursement records")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in DISBURSEMENT_STATUSES: raise HTTPException(status_code=422, detail="Unsupported disbursement status")
    approval = _latest_approval(db, req.id)
    if not approval: raise HTTPException(status_code=409, detail="Approved request is missing an approval decision")
    if _disbursed_total(db, req.id) + payload.amount > approval.amount_approved: raise HTTPException(status_code=409, detail="Disbursement exceeds approved amount")
    fund = db.query(MutualAidFund).filter(MutualAidFund.id == req.fund_id).one()
    balance = _fund_balance_read_model(db, fund)
    if payload.amount > balance["available_for_disbursement"]: raise HTTPException(status_code=409, detail="Reserve rule blocks this disbursement record")
    if payload.amount > fund.approval_threshold and current_user.role not in {"admin", "superadmin"}: raise HTTPException(status_code=403, detail="Disbursement exceeds treasurer approval threshold")
    row = MutualAidDisbursement(request_id=req.id, recipient_user_id=req.requester_user_id, amount=payload.amount, currency=req.currency, status=normalized_status, receipt_required=payload.receipt_required, scheduled_for=payload.scheduled_for, notes=payload.notes.strip(), created_by_user_id=current_user.id)
    db.add(row); db.flush()
    db.add(MutualAidDisbursementStatusHistory(disbursement_id=row.id, from_status=None, to_status=normalized_status, changed_by_user_id=current_user.id, reason="administrative tracking record created"))
    _audit(db, current_user.id, row.id, "disbursement_record_created", after=_serialize_disbursement(row))
    record_mutual_aid_notification(db, event_type="disbursement_record_created", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status, "receipt_required": payload.receipt_required})
    record_mutual_aid_notification(db, event_type="admin_disbursement_record_created", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status, "amount": payload.amount})
    if payload.receipt_required or normalized_status == "needs_receipt":
        record_mutual_aid_notification(db, event_type="receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status})
        record_mutual_aid_notification(db, event_type="admin_receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status})
    db.commit(); db.refresh(row)
    return {"ok": True, "disbursement": _serialize_disbursement(row)}

@router.post("/admin/disbursements/{disbursement_id}/status")
def update_disbursement_status(disbursement_id: int, payload: DisbursementStatusPayload, current_user: User = Depends(require_permission("mutual_aid:manage_disbursements")), db: Session = Depends(get_db)):
    _ensure_disbursement_tracking_enabled()
    row = db.query(MutualAidDisbursement).filter(MutualAidDisbursement.id == disbursement_id).first()
    if not row: raise HTTPException(status_code=404, detail="Disbursement not found")
    normalized_status = payload.status.strip().lower()
    if normalized_status not in DISBURSEMENT_STATUSES: raise HTTPException(status_code=422, detail="Unsupported disbursement status")
    before = _serialize_disbursement(row); old = row.status; row.status = normalized_status
    if normalized_status == "closed": row.closed_at = datetime.utcnow()
    req = db.query(MutualAidRequest).filter(MutualAidRequest.id == row.request_id).first()
    if normalized_status == "needs_receipt" and req:
        record_mutual_aid_notification(db, event_type="receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=req.requester_user_id, actor_user_id=current_user.id, payload={"status": normalized_status, "reason": payload.reason.strip()})
        record_mutual_aid_notification(db, event_type="admin_receipt_needed", request_id=req.id, disbursement_id=row.id, recipient_user_id=None, actor_user_id=current_user.id, audience="admin", payload={"status": normalized_status})
    db.add(MutualAidDisbursementStatusHistory(disbursement_id=row.id, from_status=old, to_status=normalized_status, changed_by_user_id=current_user.id, reason=payload.reason.strip()))
    _audit(db, current_user.id, row.id, "disbursement_status_changed", before=before, after=_serialize_disbursement(row))
    db.commit(); db.refresh(row)
    return {"ok": True, "disbursement": _serialize_disbursement(row)}
