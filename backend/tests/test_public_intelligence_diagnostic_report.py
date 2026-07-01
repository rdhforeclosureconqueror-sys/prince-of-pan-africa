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


def test_public_json_and_markdown_endpoints_are_ai_readable_without_auth():
    client, admin_id = build_client()
    created = client.post("/admin/intelligence-health/public-report", cookies=session_cookie(admin_id))
    assert created.status_code == 200
    token = created.json()["report"]["token"]

    json_response = client.get(f"/public/intelligence-diagnostics/{token}.json")
    assert json_response.status_code == 200
    body = json_response.json()
    raw = str(body)
    assert body["report_title"] == "Intelligence Diagnostic Report"
    assert body["token"] == token
    assert body["read_only"] is True
    assert body["no_write_confirmation"]["can_rerun_diagnostics"] is False
    assert body["fixture_name"] == "intelligence-health-fixture"
    assert body["regression_count"] == body["regression_summary"]["count"]
    assert "root_cause_analysis" in body
    assert "recommended_admin_actions" in body
    assert "diagnostic_history_summary" in body
    assert "previous_run_comparison" in body
    assert "debug_payload" not in raw
    assert "real.member@example.com" not in raw
    assert "password_hash" not in raw

    md_response = client.get(f"/public/intelligence-diagnostics/{token}.md")
    assert md_response.status_code == 200
    assert "text/markdown" in md_response.headers["content-type"]
    markdown = md_response.text
    assert "# Intelligence Diagnostic Report" in markdown
    assert "## Overall Health" in markdown
    assert "## Safety Confirmation" in markdown
    assert "## Layer Results" in markdown
    assert "## Regression Summary" in markdown
    assert "## Root Cause Analysis" in markdown
    assert "## Performance Metrics" in markdown
    assert "## Diagnostic History" in markdown
    assert "## Recommended Admin Actions" in markdown
    assert "debug_payload" not in markdown
    assert "real.member@example.com" not in markdown


def test_public_endpoint_invalid_and_expired_errors_are_safe():
    client, admin_id = build_client()
    invalid = client.get("/public/intelligence-diagnostics/not valid.json")
    assert invalid.status_code in (400, 404)
    assert "Traceback" not in invalid.text
    assert "stack" not in invalid.text.lower()

    created = client.post("/admin/intelligence-health/public-report", cookies=session_cookie(admin_id))
    token = created.json()["report"]["token"]

    from app.services import intelligence_health

    intelligence_health._PUBLIC_DIAGNOSTIC_REPORTS[token]["expires_at"] = "2000-01-01T00:00:00"
    expired = client.get(f"/public/intelligence-diagnostics/{token}.json")
    assert expired.status_code == 410
    assert "expired" in expired.text.lower()
    assert "Traceback" not in expired.text


def test_public_reads_do_not_execute_diagnostics_or_mutate_history():
    client, admin_id = build_client()
    created = client.post("/admin/intelligence-health/public-report", cookies=session_cookie(admin_id))
    token = created.json()["report"]["token"]

    from app.services import intelligence_health

    history_count = len(intelligence_health._DIAGNOSTIC_HISTORY)
    stored_reports = dict(intelligence_health._PUBLIC_DIAGNOSTIC_REPORTS)
    assert client.get(f"/public/intelligence-diagnostics/{token}.json").status_code == 200
    assert client.get(f"/public/intelligence-diagnostics/{token}.md").status_code == 200
    assert len(intelligence_health._DIAGNOSTIC_HISTORY) == history_count
    assert intelligence_health._PUBLIC_DIAGNOSTIC_REPORTS == stored_reports


def test_admin_diagnostic_history_remains_protected():
    client, _ = build_client()
    assert client.get("/admin/intelligence-health/history").status_code == 401


def test_public_diagnostic_complete_production_flow_json_markdown_react_and_health():
    client, admin_id = build_client()

    created = client.post("/admin/intelligence-health/public-report", cookies=session_cookie(admin_id))
    assert created.status_code == 200
    report = created.json()["report"]
    token = report["token"]
    assert report["storage_persisted"] is True

    json_response = client.get(f"/public/intelligence-diagnostics/{token}.json")
    assert json_response.status_code == 200
    json_body = json_response.json()
    assert json_body["token"] == token
    assert json_body["public_report"] is True
    assert json_body["layers"]

    markdown_response = client.get(f"/public/intelligence-diagnostics/{token}.md")
    assert markdown_response.status_code == 200
    assert "# Intelligence Diagnostic Report" in markdown_response.text
    assert json_body["fixture_name"] in markdown_response.text

    react_page_response = client.get(f"/public/intelligence-diagnostics/{token}")
    assert react_page_response.status_code == 200
    react_payload = react_page_response.json()
    assert react_payload["overall_summary"] == json_body["overall_summary"]
    assert react_payload["layers"][0]["layer"] == json_body["layers"][0]["layer"]

    health = client.get("/admin/intelligence-health/public-report/health", cookies=session_cookie(admin_id))
    assert health.status_code == 200
    checks = health.json()["checks"]
    assert checks["public_diagnostics_enabled"]["status"] == "PASS"
    assert checks["storage_working"]["status"] == "PASS"
    assert checks["token_generation_working"]["status"] == "PASS"
    assert checks["json_route_working"]["status"] == "PASS"
    assert checks["markdown_route_working"]["status"] == "PASS"
    assert checks["react_page_can_fetch_successfully"]["status"] == "PASS"
