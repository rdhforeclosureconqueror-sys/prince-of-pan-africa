import os

from fastapi.testclient import TestClient

from app.main import app


def _set_minimal_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("AUDIO_STORAGE_DIR", "/var/data/static/audio")
    monkeypatch.setenv("BOOK_COVER_STORAGE_DIR", "/var/data/static/book-covers")


def test_readiness_healthy_returns_ok(monkeypatch):
    _set_minimal_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "postgresql",
            "connected": True,
            "tables": {
                "users": True,
                "member_profiles": True,
                "activity_logs": True,
                "leadership_assessments": True,
                "audiobooks": True,
                "audiobook_chapters": True,
                "audiobook_progress": True,
                "audiobook_chapter_reflections": True,
                "audio_assets": True,
                "book_organizer_documents": True,
                "book_organizer_blocks": True,
                "book_organization_plans": True,
            },
            "seed_admin_exists": True,
            "unsafe_fallback": False,
            "ok": True,
        },
    )
    monkeypatch.setattr(verification_engine.Path, "exists", lambda self: True)
    monkeypatch.setattr(verification_engine.Path, "is_dir", lambda self: True)

    readiness = verification_engine.build_readiness_verification()
    assert readiness["status"] == "ok"


def test_readiness_missing_required_env_fails(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {"db_type": "sqlite", "connected": True, "tables": {"users": True}, "seed_admin_exists": True},
    )

    readiness = verification_engine.build_readiness_verification()
    assert readiness["status"] == "failed"


def test_readiness_detects_database_failure(monkeypatch):
    _set_minimal_env(monkeypatch)

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {"db_type": "sqlite", "connected": False, "tables": {}, "seed_admin_exists": False, "error": "db down"},
    )

    readiness = verification_engine.build_readiness_verification()
    assert readiness["status"] == "failed"
    db_check = next(item for item in readiness["details"] if item["name"] == "database_connectivity")
    assert db_check["status"] == "failed"


def test_detailed_verification_requires_permission():
    client = TestClient(app)
    response = client.get("/system/verification")
    assert response.status_code == 401


def test_public_health_does_not_leak_sensitive_config(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "super-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "super-openai-key")
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    serialized = str(body)
    assert "super-secret-value" not in serialized
    assert "super-openai-key" not in serialized
    assert "SESSION_SECRET" not in serialized
    assert "OPENAI_API_KEY" not in serialized


def test_readiness_reports_production_persistence_and_storage(monkeypatch):
    _set_minimal_env(monkeypatch)
    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "postgresql",
            "connected": True,
            "tables": {table: True for table in verification_engine.TABLES_REQUIRED},
            "seed_admin_exists": True,
            "unsafe_fallback": False,
        },
    )
    monkeypatch.setattr(verification_engine.Path, "exists", lambda self: True)
    monkeypatch.setattr(verification_engine.Path, "is_dir", lambda self: True)

    readiness = verification_engine.build_readiness_verification()

    checks = {item["name"]: item for item in readiness["details"]}
    assert checks["production_persistence"]["status"] == "ok"
    assert checks["production_persistence"]["details"]["db_type"] == "postgres"
    assert checks["render_disk_mount"]["status"] == "ok"
    assert checks["persistent_media_storage"]["status"] == "ok"


def test_readiness_fails_when_media_storage_is_not_persistent(monkeypatch):
    _set_minimal_env(monkeypatch)
    monkeypatch.setenv("AUDIO_STORAGE_DIR", "backend/app/static/audio")
    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "postgresql",
            "connected": True,
            "tables": {table: True for table in verification_engine.TABLES_REQUIRED},
            "seed_admin_exists": True,
            "unsafe_fallback": False,
        },
    )
    monkeypatch.setattr(verification_engine.Path, "exists", lambda self: True)
    monkeypatch.setattr(verification_engine.Path, "is_dir", lambda self: True)

    readiness = verification_engine.build_readiness_verification()

    storage = next(item for item in readiness["details"] if item["name"] == "persistent_media_storage")
    assert storage["status"] == "failed"
    assert storage["details"]["AUDIO_STORAGE_DIR"]["expected"] == "/var/data/static/audio"
