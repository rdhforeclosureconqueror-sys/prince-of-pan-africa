import os
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie

PRODUCTION_ORIGIN = "https://simbawaujamaa.com"


def build_client(tmp_path: Path):
    db_path = tmp_path / "test_admin_intel_health_cors.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    os.environ["ALLOWED_ORIGINS"] = "https://example.invalid"

    from app.authz import seed_rbac_defaults
    from app.database import Base, SessionLocal, engine
    from app.main import app
    from app.models import User

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = User(email="cors-diag-admin@example.com", password_hash="x", role="admin")
        db.add(admin)
        db.commit()
        seed_rbac_defaults(db)
        return TestClient(app, raise_server_exceptions=False), admin.id
    finally:
        db.close()


def test_intelligence_health_run_preflight_allows_production_origin(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.options(
        "/admin/intelligence-health/run",
        headers={
            "Origin": PRODUCTION_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_intelligence_health_run_post_includes_production_cors_header(tmp_path):
    client, admin_id = build_client(tmp_path)

    response = client.post(
        "/admin/intelligence-health/run",
        headers={"Origin": PRODUCTION_ORIGIN},
        cookies=session_cookie(admin_id),
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.json()["read_only"] is True


def test_intelligence_health_run_error_response_keeps_production_cors_header(tmp_path, monkeypatch):
    client, admin_id = build_client(tmp_path)

    from app.routes import admin as admin_routes

    def fail_diagnostic(db):
        raise RuntimeError("diagnostic runner failed")

    monkeypatch.setattr(admin_routes, "run_full_intelligence_diagnostic", fail_diagnostic)

    response = client.post(
        "/admin/intelligence-health/run",
        headers={"Origin": PRODUCTION_ORIGIN},
        cookies=session_cookie(admin_id),
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == PRODUCTION_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.json()["error"] == "internal_server_error"
