import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(review_enabled="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-review.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = review_enabled
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


def payload():
    return {"category":"housing","urgency":"urgent","requested_amount":250,"explanation":"Need short-term help with housing stability this week.","preferred_support_method":"community_follow_up","policy_consent":True}


def submit_request(client, member_id):
    request_id = client.post("/mutual-aid/requests/draft", json=payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
    client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id))
    return request_id


def test_member_cannot_access_admin_review_queue():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        submit_request(client, member_id)
        response = client.get("/mutual-aid/admin/requests", cookies=session_cookie(member_id))
        assert response.status_code == 403
    finally:
        tmp.cleanup()


def test_reviewer_can_only_access_assigned_requests_unless_admin():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        other_reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        request_id = submit_request(client, member_id)
        assigned = client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": reviewer_id}, cookies=session_cookie(admin_id))
        assert assigned.status_code == 200, assigned.text
        assert client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(reviewer_id)).status_code == 200
        assert client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(other_reviewer_id)).status_code == 404
        assert client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(admin_id)).status_code == 200
    finally:
        tmp.cleanup()


def test_conflicted_reviewer_cannot_recommend_and_more_info_changes_status_and_audits():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        request_id = submit_request(client, member_id)
        client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": reviewer_id}, cookies=session_cookie(admin_id))
        conflict = client.post(f"/mutual-aid/admin/requests/{request_id}/conflict-disclosure", json={"disclosure":"I have a household relationship with the requester."}, cookies=session_cookie(reviewer_id))
        assert conflict.status_code == 200, conflict.text
        rec = client.post(f"/mutual-aid/admin/requests/{request_id}/recommendation", json={"recommendation":"support", "notes":"Documents align with policy."}, cookies=session_cookie(reviewer_id))
        assert rec.status_code == 409
        more = client.post(f"/mutual-aid/admin/requests/{request_id}/request-more-info", json={"message":"Please upload a current bill."}, cookies=session_cookie(reviewer_id))
        assert more.status_code == 200
        assert more.json()["request"]["status"] == "more_info_requested"
        db = database.SessionLocal()
        try:
            actions = {row.action for row in db.query(models.MutualAidAuditLog).all()}
            assert {"reviewer_assigned", "conflict_disclosed", "more_info_requested"}.issubset(actions)
        finally:
            db.close()
    finally:
        tmp.cleanup()


def test_recommendation_writes_audit_log_and_no_money_routes_exist():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        request_id = submit_request(client, member_id)
        client.post(f"/mutual-aid/admin/requests/{request_id}/assign-reviewer", json={"reviewer_user_id": reviewer_id}, cookies=session_cookie(admin_id))
        rec = client.post(f"/mutual-aid/admin/requests/{request_id}/recommendation", json={"recommendation":"needs_committee_review", "notes":"Eligible for committee discussion, not approval."}, cookies=session_cookie(reviewer_id))
        assert rec.status_code == 200, rec.text
        db = database.SessionLocal()
        try:
            assert db.query(models.MutualAidAuditLog).filter(models.MutualAidAuditLog.action == "recommendation_recorded").count() == 1
        finally:
            db.close()
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payout", "payment", "wallet", "cash-balance", "reimbursement", "disbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
