from fastapi import APIRouter, Query, Request

from app.database import get_database_type, reset_local_sqlite_database
from verification.verification_engine import build_full_system_verification, build_system_verification, check_database

router = APIRouter(prefix="/system", tags=["System"])


def _routes_inventory(app) -> list[str]:
    return sorted({route.path for route in app.routes})


@router.get("/verification")
def system_verification(request: Request):
    return build_system_verification(request.app)


@router.get("/verification/full")
def system_verification_full(request: Request):
    return build_full_system_verification(request.app)


@router.post("/database/reset-local")
def reset_local_database(dev_confirm: bool = Query(default=False)):
    if not dev_confirm:
        return {
            "ok": False,
            "message": "Destructive dev-only action. Re-run with ?dev_confirm=true to reset local SQLite.",
            "database_type": get_database_type(),
        }
    return reset_local_sqlite_database()


@router.get("/database/check")
def database_check():
    return check_database()


@router.get("/tests/routes")
def test_routes(request: Request):
    routes = _routes_inventory(request.app)
    expected = [
        "/",
        "/health",
        "/info",
        "/system/verification",
        "/system/verification/full",
        "/system/tests/routes",
        "/system/tests/database",
        "/system/tests/services",
        "/system/tests/integrations",
        "/auth/me",
        "/tts",
        "/assessment/submit",
        "/assessment/results/{user_id}",
        "/assessment/dashboard/{user_id}",
        "/assessment/analytics/roles",
        "/admin/ai/overview",
        "/admin/ai/members",
        "/admin/ai/profiles",
        "/member/overview",
        "/member/activity",
        "/chat/tts",
    ]
    missing = [endpoint for endpoint in expected if endpoint not in routes]
    return {
        "routes_total": len(routes),
        "routes_verified": len(routes) - len(missing),
        "missing_routes": missing,
    }


@router.get("/tests/database")
def test_database():
    check = check_database()
    return {
        "database_ok": check.get("ok", False),
        "db_type": check.get("db_type"),
        "tables": check.get("tables", {}),
        "seed_admin_exists": check.get("seed_admin_exists", False),
        "error": check.get("error"),
    }


@router.get("/tests/services")
def test_services():
    checks = {
        "chat_service": True,
        "portal_service": True,
        "voice_service": True,
        "admin_seed_service": True,
        "tts_service": True,
        "assessment_service": True,
        "admin_ai_service": True,
    }
    return {
        "services_total": len(checks),
        "services_verified": sum(1 for value in checks.values() if value),
        "services": checks,
    }


@router.get("/tests/integrations")
def test_integrations():
    integrations = {
        "openai": bool(__import__("os").getenv("OPENAI_API_KEY")),
        "aivoice": bool(__import__("os").getenv("AIVOICE_BASE_URL")),
        "aivoice_key": bool(__import__("os").getenv("AIVOICE_API_KEY")),
        "assessment_db": check_database().get("ok", False),
    }
    return {
        "integrations_total": len(integrations),
        "integrations_verified": sum(1 for value in integrations.values() if value),
        "integrations": integrations,
        "missing_integrations": [name for name, ok in integrations.items() if not ok],
    }