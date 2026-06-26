import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app():
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-financial.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"] = "true"
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


def make_request(client, member_id, admin_id, amount=250):
    payload = {"category":"housing","urgency":"urgent","requested_amount":amount,"explanation":"Need short-term help with housing stability this week.","preferred_support_method":"community_follow_up","policy_consent":True}
    request_id = client.post("/mutual-aid/requests/draft", json=payload, cookies=session_cookie(member_id)).json()["request"]["id"]
    client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id))
    decision = {"decision":"approve", "reason_code":"eligible_need", "notes":"Governance reviewed and approved documentation.", "approved_amount":amount, "appeal_eligible":False}
    assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision, cookies=session_cookie(admin_id)).status_code == 200
    return request_id


def test_member_cannot_access_financial_controls_and_reviewer_cannot_create_disbursement():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        reviewer_id = seed_user(database, models, "mutual_aid_reviewer")
        admin_id = seed_user(database, models, "admin")
        request_id = make_request(client, member_id, admin_id)
        assert client.get("/mutual-aid/admin/financial-controls", cookies=session_cookie(member_id)).status_code == 403
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/disbursements", json={"amount": 10}, cookies=session_cookie(reviewer_id)).status_code == 403
    finally:
        tmp.cleanup()


def test_only_approved_requests_receive_disbursements_and_audit_logs_are_written():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")
        db = database.SessionLocal()
        try:
            fund = db.query(models.MutualAidFund).one(); fund.current_balance = 1000; db.commit()
        finally:
            db.close()
        payload = {"category":"food","urgency":"standard","requested_amount":100,"explanation":"Need temporary grocery support for household stability.","preferred_support_method":"community_follow_up","policy_consent":True}
        draft_id = client.post("/mutual-aid/requests/draft", json=payload, cookies=session_cookie(member_id)).json()["request"]["id"]
        assert client.post(f"/mutual-aid/admin/requests/{draft_id}/disbursements", json={"amount": 50}, cookies=session_cookie(treasurer_id)).status_code == 409
        admin_id = seed_user(database, models, "admin")
        approved_id = make_request(client, member_id, admin_id, 100)
        res = client.post(f"/mutual-aid/admin/requests/{approved_id}/disbursements", json={"amount": 50, "receipt_required": True}, cookies=session_cookie(treasurer_id))
        assert res.status_code == 200, res.text
        assert res.json()["disbursement"]["status"] == "pending"
        assert res.json()["disbursement"]["receipt_required"] is True
        db = database.SessionLocal()
        try:
            assert db.query(models.MutualAidAuditLog).filter(models.MutualAidAuditLog.action == "disbursement_record_created").count() == 1
            assert db.query(models.MutualAidDisbursementStatusHistory).count() == 1
        finally:
            db.close()
    finally:
        tmp.cleanup()


def test_reserve_rule_blocks_over_disbursement_and_no_money_routes_exist():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        request_id = make_request(client, member_id, admin_id, 100)
        db = database.SessionLocal()
        try:
            fund = db.query(models.MutualAidFund).one(); fund.current_balance = 100; fund.reserve_percent = 10; db.commit()
        finally:
            db.close()
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/disbursements", json={"amount": 95}, cookies=session_cookie(admin_id)).status_code == 409
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("/payout", "/payment", "/wallet", "cash-balance", "reimbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
