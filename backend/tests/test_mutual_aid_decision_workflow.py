import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(decisions_enabled="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-decisions.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = decisions_enabled
    os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = "false"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    import app.config as config
    import app.database as database
    importlib.reload(config); importlib.reload(database)
    import app.models as models
    import app.authz as authz
    import app.routes.mutual_aid as mutual_aid_route
    import app.main as main
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
    return {"category":"housing","urgency":"urgent","requested_amount":250,"explanation":"Need short-term help with housing stability this week.","preferred_support_method":"community_follow_up","policy_consent":True}


def submit_request(client, member_id):
    request_id = client.post("/mutual-aid/requests/draft", json=request_payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
    client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id))
    return request_id


def decision_payload(**overrides):
    payload = {"decision":"approve", "reason_code":"eligible_need", "notes":"Governance reviewed and approved documentation.", "approved_amount":125, "appeal_eligible":False, "appeal_deadline":None, "appeal_instructions":""}
    payload.update(overrides)
    return payload


def test_member_and_reviewer_without_decision_permission_cannot_decide():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        request_id = submit_request(client, member_id)
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload(), cookies=session_cookie(member_id)).status_code == 403
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload(), cookies=session_cookie(reviewer_id)).status_code == 403
    finally:
        tmp.cleanup()


def test_conflicted_admin_reviewer_cannot_decide():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = submit_request(client, member_id)
        client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": admin_id}, cookies=session_cookie(admin_id))
        conflict = client.post(f"/mutual-aid/admin/requests/{request_id}/conflict-disclosure", json={"disclosure":"I have a family relationship with the requester."}, cookies=session_cookie(admin_id))
        assert conflict.status_code == 200, conflict.text
        response = client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload(), cookies=session_cookie(admin_id))
        assert response.status_code == 409
    finally:
        tmp.cleanup()


def test_approved_decision_records_amount_history_and_audit_log():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = submit_request(client, member_id)
        response = client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload(approved_amount=200), cookies=session_cookie(admin_id))
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["request"]["status"] == "approved"
        assert body["decision"]["approved_amount"] == 200
        db = database.SessionLocal()
        try:
            assert db.query(models.MutualAidRequestStatusHistory).filter(models.MutualAidRequestStatusHistory.request_id == request_id, models.MutualAidRequestStatusHistory.to_status == "approved").count() == 1
            assert db.query(models.MutualAidAuditLog).filter(models.MutualAidAuditLog.action == "decision_recorded").count() == 1
        finally:
            db.close()
    finally:
        tmp.cleanup()


def test_not_approved_decision_records_reason_code_and_no_money_routes_exist():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = submit_request(client, member_id)
        response = client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision_payload(decision="not_approved", reason_code="outside_policy", approved_amount=0, appeal_eligible=True, appeal_instructions="Submit an appeal within 14 days."), cookies=session_cookie(admin_id))
        assert response.status_code == 200, response.text
        assert response.json()["decision"]["reason_code"] == "outside_policy"
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payout", "payment", "wallet", "cash-balance", "reimbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
