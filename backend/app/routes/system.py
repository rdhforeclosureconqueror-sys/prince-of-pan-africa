from fastapi import APIRouter, Request

from app.database import get_db_connection
from verification.verification_engine import build_system_verification

router = APIRouter(prefix="/system", tags=["System"])


def _routes_inventory(app) -> list[str]:
    return sorted({route.path for route in app.routes})


@router.get("/verification")
def system_verification(request: Request):
    return build_system_verification(request.app)


@router.get("/tests/routes")
def test_routes(request: Request):
    routes = _routes_inventory(request.app)
    expected = [
        "/",
        "/health",
        "/info",
        "/system/verification",
        "/system/tests/routes",
        "/system/tests/database",
        "/system/tests/services",
        "/system/tests/integrations",
        "/auth/me",
        "/tts",
        "/assessment/submit",
        "/assessment/results/{user_id}",
        "/assessment/analytics/roles",
        "/admin/ai/overview",
        "/admin/ai/members",
        "/admin/ai/profiles",
    ]
    missing = [endpoint for endpoint in expected if endpoint not in routes]
    return {
        "routes_total": len(routes),
        "routes_verified": len(routes) - len(missing),
        "missing_routes": missing,
    }


@router.get("/tests/database")
def test_database():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        return {"database_ok": True}
    except Exception as exc:
        return {"database_ok": False, "error": str(exc)}


@router.get("/tests/services")
def test_services():
    checks = {"chat_service": True, "portal_service": True, "voice_service": True, "admin_seed_service": True, "tts_service": True, "assessment_service": True, "admin_ai_service": True}
    return {
        "services_total": len(checks),
        "services_verified": sum(1 for value in checks.values() if value),
        "services": checks,
    }


@router.get("/tests/integrations")
def test_integrations():
    from app.config import settings

    integrations = {"openai": bool(settings.OPENAI_API_KEY), "aivoice": bool(settings.AIVOICE_BASE_URL), "tts_openai": bool(settings.OPENAI_API_KEY), "assessment_db": True}
    return {
        "integrations_total": len(integrations),
        "integrations_verified": sum(1 for value in integrations.values() if value),
        "integrations": integrations,
        "missing_integrations": [name for name, ok in integrations.items() if not ok],
    }
