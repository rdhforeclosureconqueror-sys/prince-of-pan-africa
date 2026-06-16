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


def _path_check(path: str, expected: str) -> dict[str, Any]:
    return {
        "configured": bool(path.strip()),
        "path": path,
        "expected": expected,
        "matches_expected": path.strip() == expected,
    }


def _mount_check(path: str) -> dict[str, Any]:
    mount = Path(path)
    return {
        "path": path,
        "exists": mount.exists(),
        "is_dir": mount.is_dir(),
    }


def check_database() -> dict[str, Any]:
    db_type = get_database_type()
    result: dict[str, Any] = {
        "db_type": db_type,
        "connected": False,
        "tables": {},
        "seed_admin_exists": False,
        "persistence_mode": "postgres" if db_type == "postgresql" else db_type,
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
        if is_production_like_environment() and result["unsafe_fallback"]:
            result["ok"] = False
            result["error"] = "Unsafe SQLite fallback detected for production-like environment."
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

    db_type = db_check.get("db_type")
    production_persistence_ok = bool(os.getenv("DATABASE_URL")) and db_type == "postgresql" and not db_check.get("unsafe_fallback", False)
    checks.append(
        {
            "name": "production_persistence",
            "status": "ok" if production_persistence_ok else "failed",
            "details": {
                "database_url_present": bool(os.getenv("DATABASE_URL")),
                "db_type": "postgres" if db_type == "postgresql" else db_type,
                "unsafe_fallback": db_check.get("unsafe_fallback", False),
            },
        }
    )

    render_disk = _mount_check("/var/data")
    checks.append(
        {
            "name": "render_disk_mount",
            "status": "ok" if render_disk["exists"] and render_disk["is_dir"] else "failed",
            "details": render_disk,
        }
    )

    audio_storage = _path_check(os.getenv("AUDIO_STORAGE_DIR", ""), "/var/data/static/audio")
    cover_storage = _path_check(os.getenv("BOOK_COVER_STORAGE_DIR", ""), "/var/data/static/book-covers")
    storage_ok = audio_storage["matches_expected"] and cover_storage["matches_expected"]
    checks.append(
        {
            "name": "persistent_media_storage",
            "status": "ok" if storage_ok else "failed",
            "details": {
                "AUDIO_STORAGE_DIR": audio_storage,
                "BOOK_COVER_STORAGE_DIR": cover_storage,
            },
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
