import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.database import SessionLocal, engine, get_database_type
from app.models import User
from app.services.admin_seed import ADMIN_EMAIL

TABLES_REQUIRED = ["users", "member_profiles", "activity_logs", "leadership_assessments"]


def _bool_env(name: str) -> bool:
    return bool(os.getenv(name))


def check_database() -> dict[str, Any]:
    db_type = get_database_type()
    result: dict[str, Any] = {
        "db_type": db_type,
        "connected": False,
        "tables": {},
        "seed_admin_exists": False,
    }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["connected"] = True

        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        result["tables"] = {table: table in existing for table in TABLES_REQUIRED}

        with SessionLocal() as db:
            result["seed_admin_exists"] = (
                db.query(User).filter(User.email == ADMIN_EMAIL).first() is not None
            )

        result["ok"] = result["connected"] and all(result["tables"].values())
        return result
    except Exception as exc:
        result["error"] = str(exc)
        result["ok"] = False
        return result


def _check_route_exists(app, route_path: str) -> bool:
    return route_path in {route.path for route in app.routes}


def _safe_json(response) -> dict[str, Any]:
    try:
        return response.json() if response.content else {}
    except Exception:
        return {}


def _auth_check(client: TestClient) -> dict[str, Any]:
    res = client.get("/auth/me")
    data = _safe_json(res)
    return {
        "ok": res.status_code == 200 and isinstance(data.get("user"), (dict, type(None))),
        "status_code": res.status_code,
        "has_user_key": "user" in data,
    }


def _member_check(client: TestClient) -> dict[str, Any]:
    overview = client.get("/member/overview")
    activity = client.get("/member/activity")
    o_data = _safe_json(overview)
    a_data = _safe_json(activity)
    db_driven = all(key in o_data for key in ["user", "member_profile", "summary_stats"])
    return {
        "ok": overview.status_code == 200 and activity.status_code == 200 and db_driven,
        "overview_status": overview.status_code,
        "activity_status": activity.status_code,
        "db_driven_shape": db_driven,
    }


def _leadership_check(client: TestClient) -> dict[str, Any]:
    sample_payload = {"responses": [3] * 30}
    submit = client.post("/assessment/submit", json=sample_payload)
    submit_data = _safe_json(submit)
    user_id = submit_data.get("userId")

    results_status = None
    results_ok = False
    if user_id:
        results = client.get(f"/assessment/results/{user_id}")
        results_status = results.status_code
        results_ok = results.status_code == 200

    analytics = client.get("/assessment/analytics/roles")
    return {
        "ok": submit.status_code == 200 and bool(user_id) and results_ok and analytics.status_code == 200,
        "submit_status": submit.status_code,
        "user_id_returned": bool(user_id),
        "results_status": results_status,
        "analytics_status": analytics.status_code,
    }


def _admin_ai_check(client: TestClient) -> dict[str, Any]:
    checks = {
        "overview": client.get("/admin/ai/overview").status_code,
        "members": client.get("/admin/ai/members").status_code,
        "profiles": client.get("/admin/ai/profiles").status_code,
    }
    return {"ok": all(v == 200 for v in checks.values()), "endpoints": checks}


def _tts_check(app, client: TestClient) -> dict[str, Any]:
    route_exists = _check_route_exists(app, "/chat/tts")
    env_ready = {
        "AIVOICE_API_KEY": _bool_env("AIVOICE_API_KEY"),
        "AIVOICE_BASE_URL": _bool_env("AIVOICE_BASE_URL"),
        "OPENAI_API_KEY": _bool_env("OPENAI_API_KEY"),
    }
    health_probe = client.post("/chat/tts", json={"text": "verification ping", "voice": "alloy"})

    return {
        "ok": route_exists,
        "route_exists": route_exists,
        "env_ready": env_ready,
        "health_probe_status": health_probe.status_code,
        "provider_ready": health_probe.status_code < 500,
    }


def _fitness_check() -> dict[str, Any]:
    coach_file = Path(__file__).resolve().parents[1] / ".." / "src" / "pages" / "MufasaCoach.jsx"
    coach_file = coach_file.resolve()

    if not coach_file.exists():
        return {"ok": False, "error": f"File not found: {coach_file}"}

    text_content = coach_file.read_text(encoding="utf-8")
    has_interval = "const SPEAK_INTERVAL =" in text_content
    has_same_message_guard = "message === lastMessageRef.current" in text_content
    has_time_guard = "now - lastSpokenRef.current < SPEAK_INTERVAL" in text_content

    return {
        "ok": has_interval and has_same_message_guard and has_time_guard,
        "coach_file": str(coach_file),
        "cooldown_configured": has_interval,
        "duplicate_message_guard": has_same_message_guard,
        "time_throttle_guard": has_time_guard,
    }


def _env_check() -> dict[str, Any]:
    check_vars = [
        "DATABASE_URL",
        "ALLOWED_ORIGINS",
        "CORS_ALLOWED_ORIGINS",
        "OPENAI_API_KEY",
        "AIVOICE_API_KEY",
        "AIVOICE_BASE_URL",
        "VITE_API_BASE_URL",
    ]
    status = {name: _bool_env(name) for name in check_vars}
    return {"ok": all(status.values()), "variables": status}


def _cors_and_routes_check(app) -> dict[str, Any]:
    routes = {route.path for route in app.routes}
    required_routes = [
        "/auth/me",
        "/member/overview",
        "/member/activity",
        "/assessment/submit",
        "/assessment/results/{user_id}",
        "/assessment/analytics/roles",
        "/admin/ai/overview",
        "/admin/ai/members",
        "/admin/ai/profiles",
        "/chat/tts",
        "/system/verification/full",
    ]
    missing = [r for r in required_routes if r not in routes]
    return {"ok": len(missing) == 0, "missing_routes": missing}


def build_full_system_verification(app) -> dict[str, Any]:
    with TestClient(app) as client:
        database = check_database()
        auth = _auth_check(client)
        member = _member_check(client)
        leadership = _leadership_check(client)
        admin_ai = _admin_ai_check(client)
        tts = _tts_check(app, client)
        fitness = _fitness_check()
        env = _env_check()
        cors_routes = _cors_and_routes_check(app)

    checks = {
        "database": database,
        "auth": auth,
        "member": member,
        "leadership": leadership,
        "admin_ai": admin_ai,
        "tts": tts,
        "fitness": fitness,
        "env": env,
        "cors_routes": cors_routes,
    }

    return {"ok": all(section.get("ok", False) for section in checks.values()), **checks}


def build_system_verification(app) -> dict[str, Any]:
    full = build_full_system_verification(app)
    return {
        "system_status": "OK" if full["ok"] else "DEGRADED",
        "database": full["database"],
        "environment": full["env"],
        "cors_routes": full["cors_routes"],
    }