import importlib
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(analytics="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-analytics.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"] = "true"
    os.environ["MUTUAL_AID_NOTIFICATIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_APPEALS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_ANALYTICS_ENABLED"] = analytics
    os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = "false"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    import app.config as config, app.database as database
    importlib.reload(config); importlib.reload(database)
    import app.models as models, app.authz as authz, app.routes.mutual_aid as mutual_aid_route, app.main as main
    importlib.reload(models); importlib.reload(authz); importlib.reload(mutual_aid_route); importlib.reload(main)
    database.init_db()
    return tmp, database, models, TestClient(main.app)


def seed_user(database, models, role="community_member"):
    db = database.SessionLocal()
    try:
        user = models.User(email=f"{role}-{os.urandom(3).hex()}@example.com", password_hash="x", role=role)
        db.add(user); db.commit(); db.refresh(user)
        from app.authz import seed_rbac_defaults
        seed_rbac_defaults(db)
        return user.id
    finally:
        db.close()


def payload(category="housing", urgency="urgent", amount=100):
    return {"category": category, "urgency": urgency, "requested_amount": amount, "explanation": "Need short-term support to keep household stable this week.", "preferred_support_method": "community_follow_up", "policy_consent": True}


def create_decided_request(client, member_id, admin_id, category="housing", urgency="urgent", decision="approve", amount=100):
    request_id = client.post("/mutual-aid/requests/draft", json=payload(category, urgency, amount), cookies=session_cookie(member_id)).json()["request"]["id"]
    assert client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id)).status_code == 200
    assert client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": admin_id}, cookies=session_cookie(admin_id)).status_code == 200
    decision_payload = {"decision": decision, "reason_code": "eligible_need" if decision != "not_approved" else "outside_policy", "notes": "Governance reviewed the request.", "approved_amount": amount if decision in {"approve", "partial_approve"} else 0, "appeal_eligible": decision == "not_approved", "appeal_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()}
    assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload, cookies=session_cookie(admin_id)).status_code == 200
    return request_id


def test_member_and_reviewer_denied_but_admin_governance_treasurer_allowed():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        admin_id = seed_user(database, models, "admin")
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")
        governance_id = seed_user(database, models, "governance")
        assert client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(member_id)).status_code == 403
        assert client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(reviewer_id)).status_code == 403
        assert client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(admin_id)).status_code == 200
        assert client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(treasurer_id)).status_code == 200
        assert client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(governance_id)).status_code == 200
    finally:
        tmp.cleanup()


def test_analytics_aggregate_kpis_activation_and_guardrails():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")
        approved_id = create_decided_request(client, member_id, admin_id, "housing", "urgent", "approve", 100)
        denied_id = create_decided_request(client, member_id, admin_id, "food", "standard", "not_approved", 50)
        client.post(f"/mutual-aid/requests/{denied_id}/appeals", json={"reason": "missing_context", "explanation": "Additional context supports eligibility for community mutual aid."}, cookies=session_cookie(member_id))
        db = database.SessionLocal()
        try:
            fund = db.query(models.MutualAidFund).one(); fund.current_balance = 5000
            db.add(models.MutualAidCategoryBudget(fund_id=fund.id, category="housing", budget_amount=1000, reserved_amount=100))
            db.commit()
        finally:
            db.close()
        assert client.post(f"/mutual-aid/admin/requests/{approved_id}/disbursements", json={"amount": 25}, cookies=session_cookie(treasurer_id)).status_code == 200
        data = client.get("/mutual-aid/admin/analytics/executive", cookies=session_cookie(admin_id)).json()
        assert data["totals"]["total_requests"] == 2
        assert data["totals"]["approved"] == 1
        assert data["totals"]["denied"] == 1
        assert data["totals"]["appealed"] == 1
        assert data["volume"]["by_category"]["housing"] == 1
        assert data["volume"]["by_urgency"]["urgent"] == 1
        assert data["rates"]["approval_rate"] == 50
        assert data["rates"]["appeal_rate"] == 50
        assert data["activation"]["progress_percent"] == 25
        assert data["reporting"]["csv_export_scaffold"] is True
        assert data["reporting"]["pdf_export_scaffold"] is True
        assert data["reporting"]["file_storage"] is False
        assert data["disbursements"]["by_status"]["pending"] == 1
        assert any(card["label"] == "Activation Progress" for card in data["executive_kpis"])
        route_paths = {route.path.lower() for route in client.app.routes}
        assert not any("mutual-aid" in path and any(term in path for term in ("payment", "payout", "wallet")) for path in route_paths)
    finally:
        tmp.cleanup()
