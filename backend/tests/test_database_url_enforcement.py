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


def test_production_startup_fails_if_database_url_is_sqlite(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///./prod.db')

    import app.database as database

    monkeypatch.setattr(database, 'IS_SQLITE', True)
    try:
        database.enforce_database_url_for_production()
        assert False, 'Expected RuntimeError when production DATABASE_URL is SQLite'
    except RuntimeError as exc:
        assert 'Postgres' in str(exc)
