import importlib
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app():
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-appeals.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_APPEALS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_NOTIFICATIONS_ENABLED"] = "true"
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
    return {"category":"housing","urgency":"urgent","requested_amount":250,"explanation":"Need short-term help with housing stability this week.","preferred_support_method":"community_follow_up","policy_consent":True}


def submit_request(client, member_id):
    request_id = client.post("/mutual-aid/requests/draft", json=request_payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
    client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id))
    return request_id


def decide(client, admin_id, request_id, decision="not_approved", deadline=None):
    payload = {"decision": decision, "reason_code":"outside_policy" if decision == "not_approved" else "eligible_need", "notes":"Governance reviewed the Mutual Aid request.", "approved_amount":0 if decision == "not_approved" else 100, "appeal_eligible": decision == "not_approved", "appeal_deadline": deadline or (datetime.utcnow() + timedelta(days=7)).isoformat(), "appeal_instructions":"Submit an appeal with reason and explanation."}
    return client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=payload, cookies=session_cookie(admin_id))


def appeal_payload():
    return {"reason":"missing_context", "explanation":"Additional context explains why this request meets the mutual aid policy."}


def test_member_can_appeal_only_their_own_not_approved_request_and_history_visible():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        other_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = submit_request(client, member_id)
        assert decide(client, admin_id, request_id).status_code == 200
        assert client.post(f"/mutual-aid/requests/{request_id}/appeals", json=appeal_payload(), cookies=session_cookie(other_id)).status_code == 404
        response = client.post(f"/mutual-aid/requests/{request_id}/appeals", json=appeal_payload(), cookies=session_cookie(member_id))
        assert response.status_code == 200, response.text
        appeal_id = response.json()["appeal"]["id"]
        detail = client.get(f"/mutual-aid/requests/{request_id}", cookies=session_cookie(member_id))
        assert detail.status_code == 200
        assert detail.json()["appeals"][0]["id"] == appeal_id
    finally:
        tmp.cleanup()


def test_member_cannot_appeal_approved_request_and_deadline_enforced():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        approved_id = submit_request(client, member_id)
        assert decide(client, admin_id, approved_id, decision="approve").status_code == 200
        assert client.post(f"/mutual-aid/requests/{approved_id}/appeals", json=appeal_payload(), cookies=session_cookie(member_id)).status_code == 409
        expired_id = submit_request(client, member_id)
        assert decide(client, admin_id, expired_id, deadline=(datetime.utcnow() - timedelta(days=1)).isoformat()).status_code == 200
        expired = client.post(f"/mutual-aid/requests/{expired_id}/appeals", json=appeal_payload(), cookies=session_cookie(member_id))
        assert expired.status_code == 409
        assert "deadline" in expired.json()["detail"].lower()
    finally:
        tmp.cleanup()


def test_admin_governance_can_review_appeal_with_audit_log_and_notifications_no_money_routes():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = submit_request(client, member_id)
        assert decide(client, admin_id, request_id).status_code == 200
        appeal_id = client.post(f"/mutual-aid/requests/{request_id}/appeals", json=appeal_payload(), cookies=session_cookie(member_id)).json()["appeal"]["id"]
        review = client.post(f"/mutual-aid/admin/appeals/{appeal_id}/review", json={"status":"under_review", "notes":"Governance review has started."}, cookies=session_cookie(admin_id))
        assert review.status_code == 200, review.text
        assert review.json()["appeal"]["status"] == "under_review"
        admin_detail = client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(admin_id))
        assert admin_detail.status_code == 200
        assert admin_detail.json()["appeals"][0]["status"] == "under_review"
        db = database.SessionLocal()
        try:
            actions = {row.action for row in db.query(models.MutualAidAuditLog).all()}
            events = {row.event_type for row in db.query(models.MutualAidNotification).all()}
            assert {"appeal_submitted", "appeal_reviewed"}.issubset(actions)
            assert {"appeal_submitted", "admin_appeal_submitted", "appeal_status_changed"}.issubset(events)
        finally:
            db.close()
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("/payout", "/payment", "/wallet", "cash-balance", "reimbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
