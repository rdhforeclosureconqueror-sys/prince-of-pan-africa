import os


def test_production_startup_fails_if_database_url_missing(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.delenv('DATABASE_URL', raising=False)

    from app.database import enforce_database_url_for_production

    try:
        enforce_database_url_for_production()
        assert False, 'Expected RuntimeError when DATABASE_URL is missing in production'
    except RuntimeError:
        pass


def test_local_environment_allows_sqlite_fallback(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'test')
    monkeypatch.delenv('DATABASE_URL', raising=False)

    from app.database import enforce_database_url_for_production

    enforce_database_url_for_production()
