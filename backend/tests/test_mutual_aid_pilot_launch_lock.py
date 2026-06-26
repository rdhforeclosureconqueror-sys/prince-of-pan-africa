import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(payments="false", status="Building Toward Activation", flags=True):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-launch-lock.db'}"
    values = {
        "MUTUAL_AID_REQUESTS_ENABLED": "true",
        "MUTUAL_AID_REVIEW_ENABLED": "true",
        "MUTUAL_AID_DECISIONS_ENABLED": "true",
        "MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED": "true",
        "MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED": "true",
        "MUTUAL_AID_NOTIFICATIONS_ENABLED": "true",
        "MUTUAL_AID_APPEALS_ENABLED": "true",
        "MUTUAL_AID_PILOT_HARDENING_ENABLED": "true",
        "MUTUAL_AID_PILOT_LAUNCH_LOCK_ENABLED": "true" if flags else "false",
        "ENABLE_MUTUAL_AID_PAYMENTS": payments,
        "SESSION_SECRET": "test-session-secret",
    }
    os.environ.update(values)
    import app.config as config
    import app.database as database
    importlib.reload(config); importlib.reload(database)
    import app.models as models
    import app.authz as authz
    import app.routes.mutual_aid as mutual_aid_route
    import app.main as main
    importlib.reload(models); importlib.reload(authz); importlib.reload(mutual_aid_route); importlib.reload(main)
    database.init_db()
    seed_safe_state(database, models, status)
    return tmp, database, models, TestClient(main.app)


def seed_user(database, models, role="community_member"):
    db = database.SessionLocal()
    try:
        from app.authz import seed_rbac_defaults
        seed_rbac_defaults(db)
        user = models.User(email=f"{role}-{os.urandom(3).hex()}@example.com", password_hash="x", role=role)
        db.add(user); db.commit(); db.refresh(user)
        return user.id
    finally:
        db.close()


def seed_safe_state(database, models, status):
    db = database.SessionLocal()
    try:
        fund = db.query(models.MutualAidFund).one()
        fund.status = status
        db.add(models.MutualAidPolicyVersion(version="pilot-v1", title="Pilot policy", body="Read-only pilot policy."))
        db.flush()
        policy = db.query(models.MutualAidPolicyVersion).one()
        db.add(models.MutualAidMemberAcceptance(policy_version_id=policy.id, user_id=None))
        for role in ["reviewer", "treasurer", "governance"]:
            db.add(models.MutualAidCommitteeMember(role=role, status="active"))
        db.commit()
    finally:
        db.close()


def get_lock(client, user_id):
    return client.get("/mutual-aid/admin/pilot-launch-lock/verification", cookies=session_cookie(user_id))


def test_non_admin_denied():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        assert get_lock(client, member_id).status_code == 403
    finally:
        tmp.cleanup()


def test_launch_lock_fails_if_payments_enabled():
    tmp, database, models, client = build_app(payments="true")
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_lock(client, admin_id).json()
        assert data["status"] == "no-go"
        assert any(b["key"] == "payments_disabled" for b in data["blockers"])
    finally:
        tmp.cleanup()


def test_launch_lock_fails_if_activation_status_changed_incorrectly():
    tmp, database, models, client = build_app(status="Active")
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_lock(client, admin_id).json()
        assert data["status"] == "no-go"
        assert any(b["key"] == "fund_building" for b in data["blockers"])
    finally:
        tmp.cleanup()


def test_launch_lock_fails_if_required_flags_missing():
    tmp, database, models, client = build_app(flags=False)
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_lock(client, admin_id).json()
        assert data["status"] == "no-go"
        assert any(b["key"] == "required_flags_present" for b in data["blockers"])
    finally:
        tmp.cleanup()


def test_launch_lock_passes_only_when_pilot_safe_conditions_are_met():
    tmp, database, models, client = build_app()
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_lock(client, admin_id).json()
        assert data["status"] == "go"
        assert data["ready"] is True
        assert data["blockers"] == []
    finally:
        tmp.cleanup()


def test_no_payment_payout_wallet_routes_exist():
    tmp, database, models, client = build_app()
    try:
        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payment", "payout", "wallet")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()
