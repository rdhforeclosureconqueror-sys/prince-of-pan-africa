import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app():
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-notifications.db'}"
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DECISIONS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED"] = "true"
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


def draft_payload(amount=100):
    return {"category":"food","urgency":"urgent","requested_amount":amount,"explanation":"Need short-term emergency grocery support for household stability.","preferred_support_method":"community_follow_up","policy_consent":True}


def test_notifications_created_and_visible_on_member_and_admin_detail_only():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        other_id = seed_user(database, models)
        admin_id = seed_user(database, models, "admin")
        treasurer_id = seed_user(database, models, "mutual_aid_treasurer")
        db = database.SessionLocal()
        try:
            fund = db.query(models.MutualAidFund).one(); fund.current_balance = 1000; db.commit()
        finally:
            db.close()

        request_id = client.post("/mutual-aid/requests/draft", json=draft_payload(), cookies=session_cookie(member_id)).json()["request"]["id"]
        assert client.post(f"/mutual-aid/requests/{request_id}/submit", json={}, cookies=session_cookie(member_id)).status_code == 200
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/request-more-info", json={"message":"Please add a utility notice or receipt."}, cookies=session_cookie(admin_id)).status_code == 200
        decision = {"decision":"approve", "reason_code":"eligible_need", "notes":"Approved for documented urgent need.", "approved_amount":100, "appeal_eligible":True}
        assert client.post(f"/mutual-aid/admin/requests/{request_id}/decision", json=decision, cookies=session_cookie(admin_id)).status_code == 200
        disbursed = client.post(f"/mutual-aid/admin/requests/{request_id}/disbursements", json={"amount":50, "receipt_required":True}, cookies=session_cookie(treasurer_id))
        assert disbursed.status_code == 200, disbursed.text
        disbursement_id = disbursed.json()["disbursement"]["id"]
        assert client.post(f"/mutual-aid/admin/disbursements/{disbursement_id}/status", json={"status":"needs_receipt", "reason":"Receipt reminder needed."}, cookies=session_cookie(treasurer_id)).status_code == 200

        db = database.SessionLocal()
        try:
            events = {row.event_type for row in db.query(models.MutualAidNotification).all()}
            assert {"request_submitted", "more_information_requested", "decision_recorded", "disbursement_record_created", "receipt_needed", "appeal_window_reminder"}.issubset(events)
            assert all(row.delivery_status == "recorded_only" and row.channels == [] for row in db.query(models.MutualAidNotification).all())
        finally:
            db.close()

        member_detail = client.get(f"/mutual-aid/requests/{request_id}", cookies=session_cookie(member_id))
        assert member_detail.status_code == 200
        assert {n["event_type"] for n in member_detail.json()["notifications"]} >= {"request_submitted", "receipt_needed"}
        assert all(n["recipient_user_id"] == member_id for n in member_detail.json()["notifications"])
        assert client.get(f"/mutual-aid/requests/{request_id}", cookies=session_cookie(other_id)).status_code == 404
        admin_detail = client.get(f"/mutual-aid/admin/requests/{request_id}", cookies=session_cookie(admin_id))
        assert admin_detail.status_code == 200
        assert any(n["audience"] == "admin" for n in admin_detail.json()["notifications"])
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("/payout", "/payment", "/wallet", "cash-balance", "reimbursement")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
