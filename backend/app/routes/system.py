from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_database_type, reset_local_sqlite_database
from app.dependencies.auth import is_local_or_dev_environment, require_permission
from verification.verification_engine import build_readiness_verification, check_database

router = APIRouter(prefix="/system", tags=["System"])


def _routes_inventory(app) -> list[str]:
    return sorted({route.path for route in app.routes})


@router.get("/verification")
def system_verification(
    request: Request, _: None = Depends(require_permission("system:read_verification"))
):
    return build_readiness_verification()


@router.get("/verification/full")
def system_verification_full(
    request: Request, _: None = Depends(require_permission("system:read_verification"))
):
    """Backward-compatible alias retained for older frontend/tests."""
    return build_readiness_verification()


@router.post("/database/reset-local")
def reset_local_database(
    dev_confirm: bool = Query(default=False),
    _: None = Depends(require_permission("system:run_dev_reset")),
):
    if not is_local_or_dev_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is disabled outside local/dev/test environments",
        )

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
        "/api/skill-world/audio",
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
    readiness = build_readiness_verification()
    checks = {item["name"]: item["status"] for item in readiness["details"]}
    return {
        "services_total": len(checks),
        "services_verified": sum(1 for value in checks.values() if value == "ok"),
        "services": checks,
        "status": readiness["status"],
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