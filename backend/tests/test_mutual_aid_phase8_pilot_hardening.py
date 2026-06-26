import importlib
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app():
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-phase8.db'}"
    os.environ["ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION"] = "true"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"] = "true"
    os.environ["MUTUAL_AID_NOTIFICATIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_APPEALS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_PILOT_HARDENING_ENABLED"] = "true"
    os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = "false"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    import app.config as config
    import app.database as database
    importlib.reload(config); importlib.reload(database)
    import app.models as models
    import app.authz as authz
    import app.services.mutual_aid as mutual_aid_service
    import app.routes.mutual_aid as mutual_aid_route
    import app.main as main
    importlib.reload(models); importlib.reload(authz); importlib.reload(mutual_aid_service); importlib.reload(mutual_aid_route); importlib.reload(main)
    database.init_db()
    db = database.SessionLocal()
    try:
        authz.seed_rbac_defaults(db)
        fund = mutual_aid_service.seed_default_mutual_aid_fund(db)
        fund.current_balance = 5000
        fund.available_balance = 5000
        fund.status = mutual_aid_service.MUTUAL_AID_BUILDING_STATUS
        fund.activation_threshold = mutual_aid_service.MUTUAL_AID_ACTIVATION_THRESHOLD
        db.commit()
    finally:
        db.close()
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


def request_payload(amount=250):
    return {"category":"housing","urgency":"urgent","requested_amount":amount,"explanation":"Need short-term help with housing stability and utilities this week.","preferred_support_method":"community_follow_up","policy_consent":True}


def test_phase8_pilot_readiness_endpoint_is_admin_only_and_preserves_guardrails():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        assert client.get("/mutual-aid/admin/pilot-readiness/verification", cookies=session_cookie(member_id)).status_code == 403
        response = client.get("/mutual-aid/admin/pilot-readiness/verification", cookies=session_cookie(admin_id))
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["pilot_hardening_enabled"] is True
        assert body["ready"] is True
        assert body["activation_status"] == "Building Toward Activation"
        assert body["activation_threshold"] == 20000
        assert body["money_route_findings"] == []
        labels = {check["key"]: check["passed"] for check in body["checks"]}
        assert labels["payments_disabled"] is True
        assert labels["no_live_money_routes"] is True
    finally:
        tmp.cleanup()


def test_phase8_end_to_end_pilot_flow_records_notifications_audit_history_and_appeal():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        admin_id = seed_user(database, models, "admin")
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")

        draft = client.post("/mutual-aid/requests/draft", json=request_payload(), cookies=session_cookie(member_id))
        assert draft.status_code == 200, draft.text
        request_id = draft.json()["request"]["id"]
        submitted = client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id))
        assert submitted.status_code == 200, submitted.text

        assigned = client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": reviewer_id}, cookies=session_cookie(admin_id))
        assert assigned.status_code == 200, assigned.text
        recommendation = client.post(f"/mutual-aid/admin/requests/{request_id}/recommendation", json={"recommendation":"approve", "notes":"Reviewer confirms policy eligibility for pilot support."}, cookies=session_cookie(reviewer_id))
        assert recommendation.status_code == 200, recommendation.text

        decision_payload = {"decision":"approve", "reason_code":"eligible_need", "notes":"Governance/admin approved a tracked pilot support record.", "approved_amount":250, "appeal_eligible":False, "appeal_deadline":None, "appeal_instructions":""}
        decision = client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload, cookies=session_cookie(admin_id))
        assert decision.status_code == 200, decision.text
        disbursement = client.post(f"/mutual-aid/admin/requests/{request_id}/disbursements", json={"amount":200, "status":"scheduled", "receipt_required":True, "notes":"Manual tracking only; no payout execution."}, cookies=session_cookie(treasurer_id))
        assert disbursement.status_code == 200, disbursement.text

        appeal_request = client.post("/mutual-aid/requests/draft", json=request_payload(100), cookies=session_cookie(member_id)).json()["request"]["id"]
        assert client.post(f"/mutual-aid/requests/{appeal_request}/submit", json={}, cookies=session_cookie(member_id)).status_code == 200
        denial_payload = {"decision":"not_approved", "reason_code":"outside_policy", "notes":"Denied for appeal path coverage.", "approved_amount":0, "appeal_eligible":True, "appeal_deadline":(datetime.utcnow() + timedelta(days=7)).isoformat(), "appeal_instructions":"Submit appeal context."}
        assert client.post(f"/mutual-aid/admin/requests/{appeal_request}/decision", json=denial_payload, cookies=session_cookie(admin_id)).status_code == 200
        appeal = client.post(f"/mutual-aid/requests/{appeal_request}/appeals", json={"reason":"missing_context", "explanation":"Additional details show eligibility should be reconsidered."}, cookies=session_cookie(member_id))
        assert appeal.status_code == 200, appeal.text

        detail = client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(admin_id))
        assert detail.status_code == 200
        assert detail.json()["status_history"]
        assert detail.json()["notifications"]

        db = database.SessionLocal()
        try:
            actions = {row.action for row in db.query(models.MutualAidAuditLog).all()}
            events = {row.event_type for row in db.query(models.MutualAidNotification).all()}
            statuses = [row.to_status for row in db.query(models.MutualAidRequestStatusHistory).all()]
            assert {"submitted", "reviewer_assigned", "recommendation_recorded", "decision_recorded", "disbursement_record_created", "appeal_submitted"}.issubset(actions)
            assert {"request_submitted", "admin_request_submitted", "decision_recorded", "disbursement_record_created", "appeal_submitted"}.issubset(events)
            assert {"draft", "submitted", "under_review", "approved", "not_approved"}.issubset(set(statuses))
        finally:
            db.close()

        route_paths = {route.path.lower() for route in client.app.routes}
        assert not any("mutual-aid" in path and any(term in path for term in ("payment", "payout", "wallet")) for path in route_paths)
    finally:
        tmp.cleanup()
