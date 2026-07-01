import os
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def build_client():
    db_path = Path("/tmp/test_public_intel_diag.db")
    if db_path.exists():
        db_path.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["SESSION_SECRET"] = "test-session-secret"

    from app import models  # noqa: F401
    from app.authz import seed_rbac_defaults
    from app.database import Base, SessionLocal, engine
    from app.main import app
    from app.models import User

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = User(email="public-diag-admin@example.com", password_hash="x", role="admin")
        member = User(email="real.member@example.com", password_hash="x", role="member")
        db.add_all([admin, member])
        db.commit()
        seed_rbac_defaults(db)
        return TestClient(app), admin.id
    finally:
        db.close()


def test_public_report_workflow_safety_boundaries():
    client, admin_id = build_client()

    assert client.post("/admin/intelligence-health/public-report").status_code == 401

    created = client.post("/admin/intelligence-health/public-report", cookies=session_cookie(admin_id))
    assert created.status_code == 200
    report = created.json()["report"]
    token = report["token"]
    assert len(token) >= 32

    public = client.get(f"/public/intelligence-diagnostics/{token}")
    assert public.status_code == 200
    body = public.json()
    raw = str(body)

    assert body["public_report"] is True
    assert body["read_only"] is True
    assert body["no_write_confirmation"] == {
        "production_writes": 0,
        "workflow_execution": False,
        "notification_count": 0,
        "assignment_count": 0,
        "persistence_of_intelligence_outputs": False,
        "can_rerun_diagnostics": False,
        "admin_api_exposed": False,
    }
    assert "real.member@example.com" not in raw
    assert "diagnostic-admin@example.test" not in raw
    assert "debug_payload" not in raw
    assert "password_hash" not in raw
    assert "auth" not in raw.lower()

    layer_names = [layer["layer"] for layer in body["layers"]]
    assert layer_names == [
        "Member Intelligence",
        "Society Intelligence",
        "Institution Intelligence",
        "Opportunity Intelligence",
        "Predictive Intelligence",
        "Decision Support",
        "Execution Planning",
        "Execution Intelligence",
        "Institutional Memory",
        "Institutional Learning",
    ]
    assert body["fixture_name"] == "intelligence-health-fixture"
    assert body["fixture_version"] == "v1"
    assert body["expected_vs_actual_summary"]
    assert "expires_at" in body

    assert client.post(f"/public/intelligence-diagnostics/{token}").status_code == 405
    assert client.post("/admin/intelligence-health/run").status_code == 401
