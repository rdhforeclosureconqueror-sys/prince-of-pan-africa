import importlib
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(observability="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-observability.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"] = "true"
    os.environ["MUTUAL_AID_NOTIFICATIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_APPEALS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_OBSERVABILITY_ENABLED"] = observability
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


def request_payload():
    return {"category": "housing", "urgency": "urgent", "requested_amount": 125, "explanation": "Need short-term support to keep household stable this week.", "preferred_support_method": "community_follow_up", "policy_consent": True}


def seed_operational_records(client, member_id, admin_id, treasurer_id):
    request_id = client.post("/mutual-aid/requests/draft", json=request_payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
    assert client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id)).status_code == 200
    assert client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": admin_id}, cookies=session_cookie(admin_id)).status_code == 200
    decision_payload = {"decision": "not_approved", "reason_code": "outside_policy", "notes": "Governance reviewed the request.", "approved_amount": 0, "appeal_eligible": True, "appeal_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()}
    assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload, cookies=session_cookie(admin_id)).status_code == 200
    assert client.post(f"/mutual-aid/requests/{request_id}/appeals", json={"reason": "missing_context", "explanation": "Additional context supports eligibility for community mutual aid."}, cookies=session_cookie(member_id)).status_code == 200
    # Tracking record only: no route executes payout or moves money.
    approved_id = client.post("/mutual-aid/requests/draft", json=request_payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
    client.post(f"/mutual-aid/requests/{approved_id}/submit", json={}, cookies=session_cookie(member_id))
    client.post(f"/mutual-aid/admin/requests/{approved_id}/decision", json={"decision": "approve", "reason_code": "eligible_need", "notes": "Approved for tracking record test.", "approved_amount": 50}, cookies=session_cookie(admin_id))
    assert client.post(f"/mutual-aid/admin/requests/{approved_id}/disbursements", json={"amount": 25}, cookies=session_cookie(treasurer_id)).status_code == 200


def test_observability_access_and_metrics_endpoints():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        admin_id = seed_user(database, models, "admin")
        governance_id = seed_user(database, models, "governance")
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")
        seed_operational_records(client, member_id, admin_id, treasurer_id)

        assert client.get("/mutual-aid/admin/operations/dashboard", cookies=session_cookie(member_id)).status_code == 403
        assert client.get("/mutual-aid/admin/operations/dashboard", cookies=session_cookie(reviewer_id)).status_code == 403
        dashboard = client.get("/mutual-aid/admin/operations/dashboard", cookies=session_cookie(admin_id))
        assert dashboard.status_code == 200
        data = dashboard.json()
        assert data["request_lifecycle"]["total_requests"] == 2
        assert data["notification_delivery_statistics"]["recorded_only"] is True
        assert data["financial_operational_metrics"]["execution_enabled"] is False
        assert data["audit_event_metrics"]["total_events"] > 0
        assert data["health"]["status"] == "healthy"
        assert data["feature_flags"]["MUTUAL_AID_OBSERVABILITY_ENABLED"] is True
        assert data["export_scaffold"]["preview_only"] is True

        report = client.get("/mutual-aid/admin/operations/reports", cookies=session_cookie(governance_id))
        assert report.status_code == 200
        treasurer_report = client.get("/mutual-aid/admin/operations/reports", cookies=session_cookie(treasurer_id)).json()
        assert treasurer_report["scope"] == "financial_operational_metrics_only"
        assert "request_lifecycle" not in treasurer_report

        metrics = client.get("/mutual-aid/admin/operations/metrics", cookies=session_cookie(admin_id)).json()
        assert metrics["error_rate_reporting"]["route_guardrail_violations"] == 0
        prom = client.get("/mutual-aid/admin/operations/prometheus", cookies=session_cookie(admin_id))
        assert prom.status_code == 200
        assert "mutual_aid_requests_total 2" in prom.text
        assert client.get("/mutual-aid/admin/operations/health", cookies=session_cookie(admin_id)).json()["status"] == "healthy"
        preview = client.get("/mutual-aid/admin/operations/report-preview", cookies=session_cookie(governance_id)).json()
        assert preview["preview_only"] is True and preview["download_url"] is None
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payment", "payout", "wallet", "reimbursement", "star", "black-dollar", "black_dollar", "ownership", "banking")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()


def test_observability_feature_flag_disabled_returns_404():
    tmp, database, models, client = build_app("false")
    try:
        admin_id = seed_user(database, models, "admin")
        assert client.get("/mutual-aid/admin/operations/health", cookies=session_cookie(admin_id)).status_code == 404
    finally:
        tmp.cleanup()
