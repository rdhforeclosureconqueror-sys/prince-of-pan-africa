import os
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text

from app.database import (
    SessionLocal,
    engine,
    get_database_type,
    is_production_like_environment,
    is_unsafe_sqlite_fallback,
)
from app.models import Permission, Role, User
from app.services.admin_seed import ADMIN_EMAIL
from app.session import SessionValidationError, get_session_secret

TABLES_REQUIRED = [
    "users",
    "member_profiles",
    "activity_logs",
    "leadership_assessments",
    "audiobooks",
    "audiobook_chapters",
    "audiobook_progress",
    "audiobook_chapter_reflections",
    "audio_assets",
    "book_organizer_documents",
    "book_organizer_blocks",
    "book_organization_plans",
]


def _bool_env(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def _status_from_checks(checks: list[dict[str, Any]]) -> str:
    if any(check.get("status") == "failed" for check in checks):
        return "failed"
    if any(check.get("status") == "degraded" for check in checks):
        return "degraded"
    return "ok"


def check_database() -> dict[str, Any]:
    db_type = get_database_type()
    result: dict[str, Any] = {
        "db_type": db_type,
        "connected": False,
        "tables": {},
        "seed_admin_exists": False,
        "persistence_mode": "postgres" if db_type == "postgres" else db_type,
        "database_url_present": _bool_env("DATABASE_URL"),
        "unsafe_fallback": is_unsafe_sqlite_fallback(),
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
        if is_production_like_environment() and (not result["database_url_present"] or db_type != "postgres"):
            result["ok"] = False
            result["error"] = "Production persistence requires DATABASE_URL backed by Postgres."
        return result
    except Exception as exc:
        result["error"] = str(exc)
        result["ok"] = False
        return result


def build_readiness_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    db_check = check_database()
    checks.append(
        {
            "name": "database_connectivity",
            "status": "ok" if db_check.get("connected") else "failed",
            "details": {
                "db_type": db_check.get("db_type"),
                "connected": db_check.get("connected", False),
                "database_url_present": db_check.get("database_url_present", _bool_env("DATABASE_URL")),
                "persistence_mode": db_check.get("persistence_mode"),
                "error": db_check.get("error"),
            },
        }
    )

    table_ok = all(db_check.get("tables", {}).values()) if db_check.get("tables") else False
    checks.append(
        {
            "name": "migration_tables",
            "status": "ok" if table_ok else "failed",
            "details": {"required_tables": db_check.get("tables", {})},
        }
    )

    checks.append(
        {
            "name": "rbac_seed_availability",
            "status": "ok" if db_check.get("seed_admin_exists") else "degraded",
            "details": {"seed_admin_exists": db_check.get("seed_admin_exists", False)},
        }
    )

    required_env = ["DATABASE_URL", "SESSION_SECRET"]
    required_presence = {name: _bool_env(name) for name in required_env}
    missing_required = [name for name, present in required_presence.items() if not present]
    checks.append(
        {
            "name": "required_environment",
            "status": "ok" if not missing_required else "failed",
            "details": {
                "required_present": required_presence,
                "missing_required": missing_required,
            },
        }
    )


    deployed = is_production_like_environment()
    persistence_status = "ok"
    persistence_errors: list[str] = []
    if deployed and not _bool_env("DATABASE_URL"):
        persistence_status = "failed"
        persistence_errors.append("DATABASE_URL is missing in a deployed/production-like environment")
    if deployed and db_check.get("db_type") != "postgres":
        persistence_status = "failed"
        persistence_errors.append("Deployed backend is not using Postgres")
    checks.append(
        {
            "name": "production_persistence",
            "status": persistence_status,
            "details": {
                "deployed_environment": deployed,
                "db_type": db_check.get("db_type"),
                "database_url_present": _bool_env("DATABASE_URL"),
                "errors": persistence_errors,
            },
        }
    )

    audio_storage_dir = os.getenv("AUDIO_STORAGE_DIR", "").strip()
    repo_root = Path(__file__).resolve().parents[2]
    audio_status = "ok"
    audio_error = None
    if deployed and not audio_storage_dir:
        audio_status = "failed"
        audio_error = "AUDIO_STORAGE_DIR is required in deployed environments so generated audio is not written to ephemeral app storage."
    elif deployed:
        audio_path = Path(audio_storage_dir).expanduser()
        try:
            resolved_audio = audio_path.resolve(strict=False)
            resolved_repo = repo_root.resolve(strict=False)
            if resolved_audio == resolved_repo or resolved_repo in resolved_audio.parents:
                audio_status = "failed"
                audio_error = "AUDIO_STORAGE_DIR points inside the application checkout; use a Render persistent disk path such as /var/data/static/audio."
        except Exception as exc:
            audio_status = "failed"
            audio_error = str(exc)
    checks.append(
        {
            "name": "durable_audio_storage",
            "status": audio_status,
            "details": {"audio_storage_dir": audio_storage_dir, "error": audio_error},
        }
    )

    external_vars = ["OPENAI_API_KEY", "AIVOICE_BASE_URL", "AIVOICE_API_KEY"]
    external_presence = {name: _bool_env(name) for name in external_vars}
    checks.append(
        {
            "name": "external_api_configuration",
            "status": "ok" if any(external_presence.values()) else "degraded",
            "details": {"configured": external_presence},
        }
    )

    session_secret_status = "ok"
    session_error = None
    try:
        secret = get_session_secret()
        if len(secret.strip()) < 32:
            session_secret_status = "degraded"
            session_error = "SESSION_SECRET length is below recommended minimum of 32 characters"
    except SessionValidationError as exc:
        session_secret_status = "failed"
        session_error = str(exc)

    checks.append(
        {
            "name": "session_secret_validation",
            "status": session_secret_status,
            "details": {"error": session_error},
        }
    )

    static_dir = Path(__file__).resolve().parents[1] / "app" / "static"
    fs_status = "ok"
    fs_error = None
    try:
        static_dir.mkdir(parents=True, exist_ok=True)
        probe = static_dir / ".readiness_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception as exc:
        fs_status = "failed"
        fs_error = str(exc)

    checks.append(
        {
            "name": "filesystem_write_access",
            "status": fs_status,
            "details": {
                "path": str(static_dir),
                "error": fs_error,
            },
        }
    )

    return {
        "status": _status_from_checks(checks),
        "ok": _status_from_checks(checks) == "ok",
        "details": checks,
    }
