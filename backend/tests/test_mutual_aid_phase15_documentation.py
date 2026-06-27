import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_app(documentation="true", payments="false"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'ma-phase15.db'}"
    os.environ["MUTUAL_AID_DOCUMENTATION_ENABLED"] = documentation
    os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = payments
    os.environ["SESSION_SECRET"] = "test-session-secret"
    import app.config as config, app.database as database
    importlib.reload(config); importlib.reload(database)
    import app.models as models, app.authz as authz, app.services.mutual_aid as service, app.routes.mutual_aid as route, app.main as main
    importlib.reload(models); importlib.reload(authz); importlib.reload(service); importlib.reload(route); importlib.reload(main)
    database.init_db()
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


def test_phase15_documentation_rbac_and_content():
    tmp, database, models, client = build_app()
    try:
        member = seed_user(database, models)
        reviewer = seed_user(database, models, "mutual_aid_reviewer")
        treasurer = seed_user(database, models, "mutual_aid_treasurer")
        governance = seed_user(database, models, "mutual_aid_governance")
        admin = seed_user(database, models, "admin")

        assert client.get("/mutual-aid/documentation", cookies=session_cookie(member)).status_code == 403

        reviewer_docs = client.get("/mutual-aid/documentation", cookies=session_cookie(reviewer)).json()["documents"]
        assert [doc["slug"] for doc in reviewer_docs] == ["reviewer-training-guide"]
        assert client.get("/mutual-aid/documentation/treasurer-operations-guide", cookies=session_cookie(reviewer)).status_code == 403

        treasurer_docs = client.get("/mutual-aid/documentation", cookies=session_cookie(treasurer)).json()["documents"]
        assert [doc["slug"] for doc in treasurer_docs] == ["treasurer-operations-guide"]

        governance_docs = client.get("/mutual-aid/documentation", cookies=session_cookie(governance)).json()["documents"]
        assert [doc["slug"] for doc in governance_docs] == ["governance-decision-handbook"]

        admin_docs = client.get("/mutual-aid/documentation", cookies=session_cookie(admin)).json()["documents"]
        slugs = {doc["slug"] for doc in admin_docs}
        assert "administrator-operations-manual" in slugs
        assert "pilot-completion-report" in slugs
        detail = client.get("/mutual-aid/documentation/api-endpoint-documentation", cookies=session_cookie(admin)).json()
        assert detail["document"]["read_only"] is True
        assert "Final readiness" in " ".join(detail["document"]["sections"])
    finally:
        tmp.cleanup()


def test_final_readiness_and_completion_dashboard_are_read_only_and_complete():
    tmp, database, models, client = build_app()
    try:
        admin = seed_user(database, models, "admin")
        readiness = client.get("/mutual-aid/admin/final-readiness/verification", cookies=session_cookie(admin))
        assert readiness.status_code == 200
        data = readiness.json()
        assert data["complete"] is True
        assert data["document_count"] == 19
        assert data["forbidden_route_findings"] == []

        dashboard = client.get("/mutual-aid/admin/completion-dashboard", cookies=session_cookie(admin)).json()
        assert dashboard["read_only"] is True
        assert dashboard["dashboard"]["mutations_enabled"] is False
        assert dashboard["dashboard"]["write_actions"] == []

        route_paths = {route.path.lower() for route in client.app.routes}
        forbidden = ("payment", "payout", "wallet", "reimbursement", "star", "black-dollar", "black_dollar", "ownership", "banking")
        assert not any("mutual-aid" in path and any(term in path for term in forbidden) for path in route_paths)
    finally:
        tmp.cleanup()


def test_documentation_flag_disabled_returns_404():
    tmp, database, models, client = build_app(documentation="false")
    try:
        admin = seed_user(database, models, "admin")
        assert client.get("/mutual-aid/documentation", cookies=session_cookie(admin)).status_code == 404
        assert client.get("/mutual-aid/admin/final-readiness/verification", cookies=session_cookie(admin)).status_code == 404
    finally:
        tmp.cleanup()
