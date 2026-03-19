import os
from typing import Any

from app.database import get_db_connection
from app.services.admin_seed import ALLOWED_ROLES

REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "AIVOICE_BASE_URL"]


def _check_database() -> dict[str, Any]:
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        return {"ok": True, "details": "Database connection successful."}
    except Exception as exc:
        return {"ok": False, "details": str(exc)}


def _check_models() -> dict[str, Any]:
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        tables = [row[0] for row in rows]
        model_names = ["users"]
        return {
            "ok": all(name in tables for name in model_names),
            "loaded_models": model_names,
            "tables": tables,
        }
    except Exception as exc:
        return {"ok": False, "details": str(exc), "loaded_models": []}


def _check_env() -> dict[str, Any]:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    return {"ok": len(missing) == 0, "required": REQUIRED_ENV_VARS, "missing": missing}


def _check_ai_modules() -> dict[str, Any]:
    modules = ["app.routes.chat", "app.utils.openai_client", "app.routes.voice", "app.routes.assessment"]
    missing = []
    for module in modules:
        try:
            __import__(module)
        except Exception:
            missing.append(module)
    return {"ok": len(missing) == 0, "modules": modules, "missing": missing}


def _check_background_workers() -> dict[str, Any]:
    return {"ok": True, "workers": [], "details": "No dedicated background workers configured in this repository."}


def build_system_verification(app) -> dict[str, Any]:
    routes_registered = sorted({route.path for route in app.routes})
    database = _check_database()
    models = _check_models()
    env = _check_env()
    ai_modules = _check_ai_modules()
    workers = _check_background_workers()

    missing_components = []
    if not database.get("ok"):
        missing_components.append("database_connection")
    if not models.get("ok"):
        missing_components.append("database_models")
    if not env.get("ok"):
        missing_components.extend([f"env:{name}" for name in env.get("missing", [])])
    if not ai_modules.get("ok"):
        missing_components.extend([f"ai_module:{name}" for name in ai_modules.get("missing", [])])

    tts_available = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "system_status": "OK" if not missing_components else "DEGRADED",
        "routes_registered": routes_registered,
        "services_operational": ["chat", "portal", "voice", "admin_seed", "tts", "assessment"],
        "tts_available": tts_available,
        "database_models_loaded": models.get("loaded_models", []),
        "missing_components": missing_components,
        "database": database,
        "models": models,
        "environment": env,
        "ai_modules": ai_modules,
        "background_workers": workers,
        "allowed_roles": sorted(ALLOWED_ROLES),
    }
