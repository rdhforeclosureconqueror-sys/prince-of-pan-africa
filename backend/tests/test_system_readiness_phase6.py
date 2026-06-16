import os

from fastapi.testclient import TestClient

from app.main import app


def _set_minimal_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)


def test_readiness_healthy_returns_ok(monkeypatch):
    _set_minimal_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "postgres",
            "connected": True,
            "tables": {table: True for table in verification_engine.TABLES_REQUIRED},
            "seed_admin_exists": True,
            "database_url_present": True,
            "persistence_mode": "postgres",
            "ok": True,
        },
    )

    monkeypatch.setenv("AUDIO_STORAGE_DIR", "/var/data/static/audio")
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
    persistence = next(item for item in readiness["details"] if item["name"] == "production_persistence")
    assert persistence["status"] == "failed"


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


def test_deployed_sqlite_is_critical_failure(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("AUDIO_STORAGE_DIR", "/var/data/static/audio")

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "sqlite",
            "connected": True,
            "tables": {table: True for table in verification_engine.TABLES_REQUIRED},
            "seed_admin_exists": True,
            "database_url_present": True,
            "persistence_mode": "sqlite",
            "ok": False,
        },
    )

    readiness = verification_engine.build_readiness_verification()
    persistence = next(item for item in readiness["details"] if item["name"] == "production_persistence")
    assert readiness["status"] == "failed"
    assert persistence["status"] == "failed"
    assert persistence["details"]["db_type"] == "sqlite"


def test_deployed_audio_storage_inside_repo_fails(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("AUDIO_STORAGE_DIR", str(os.getcwd() + "/backend/app/static/audio"))

    from verification import verification_engine

    monkeypatch.setattr(
        verification_engine,
        "check_database",
        lambda: {
            "db_type": "postgres",
            "connected": True,
            "tables": {table: True for table in verification_engine.TABLES_REQUIRED},
            "seed_admin_exists": True,
            "database_url_present": True,
            "persistence_mode": "postgres",
            "ok": True,
        },
    )

    readiness = verification_engine.build_readiness_verification()
    storage = next(item for item in readiness["details"] if item["name"] == "durable_audio_storage")
    assert readiness["status"] == "failed"
    assert storage["status"] == "failed"
