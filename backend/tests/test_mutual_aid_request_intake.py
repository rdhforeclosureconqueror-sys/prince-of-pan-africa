import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(enabled="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = enabled
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


def test_flag_defaults_closed_and_requests_404_when_disabled():
    tmp, database, models, client = build_app("false")
    try:
        user_id = seed_user(database, models)
        res = client.post("/mutual-aid/requests/draft", json=payload(), cookies=session_cookie(user_id))
        assert res.status_code == 404
    finally:
        tmp.cleanup()


def test_member_can_draft_submit_view_and_audit_without_payments():
    tmp, database, models, client = build_app("true")
    try:
        user_id = seed_user(database, models)
        draft = client.post("/mutual-aid/requests/draft", json=payload(), cookies=session_cookie(user_id))
        assert draft.status_code == 200, draft.text
        request_id = draft.json()["request"]["id"]
        submitted = client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(user_id))
        assert submitted.status_code == 200
        assert submitted.json()["request"]["status"] == "submitted"
        viewed = client.get(f"/mutual-aid/requests/{request_id}", cookies=session_cookie(user_id))
        assert viewed.status_code == 200
        db = database.SessionLocal()
        try:
            actions = {row.action for row in db.query(models.MutualAidAuditLog).all()}
            assert {"draft_saved", "submitted", "status_changed"}.issubset(actions)
            assert db.query(models.MutualAidDisbursement).count() == 0
        finally:
            db.close()
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payout", "payment", "wallet", "cash-balance", "reimbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()


def test_member_cannot_view_another_member_request_and_admin_can_list():
    tmp, database, models, client = build_app("true")
    try:
        member_id = seed_user(database, models)
        other_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = client.post("/mutual-aid/requests/draft", json=payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
        assert client.get(f"/mutual-aid/requests/{request_id}", cookies=session_cookie(other_id)).status_code == 404
        listed = client.get("/mutual-aid/admin/requests", cookies=session_cookie(admin_id))
        assert listed.status_code == 200
        assert len(listed.json()["requests"]) == 1
    finally:
        tmp.cleanup()


def test_validation_requires_policy_consent_and_document_metadata_audits():
    tmp, database, models, client = build_app("true")
    try:
        user_id = seed_user(database, models)
        bad = payload(); bad["policy_consent"] = False
        assert client.post("/mutual-aid/requests/draft", json=bad, cookies=session_cookie(user_id)).status_code == 422
        request_id = client.post("/mutual-aid/requests/draft", json=payload(), cookies=session_cookie(user_id)).json()["request"]["id"]
        doc = client.post(f"/mutual-aid/requests/{request_id}/documents/metadata", json={"filename":"lease.pdf","content_type":"application/pdf","file_size":123}, cookies=session_cookie(user_id))
        assert doc.status_code == 200
        db = database.SessionLocal()
        try:
            assert db.query(models.MutualAidRequestDocument).count() == 1
            assert db.query(models.MutualAidAuditLog).filter(models.MutualAidAuditLog.action == "document_metadata_added").count() == 1
        finally:
            db.close()
    finally:
        tmp.cleanup()
