import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_SQLITE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mufasa.db"))


def is_production_like_environment() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return env not in {"", "local", "dev", "development", "test", "testing"}


DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


def _normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://") and "+" not in raw_url.split("://", 1)[0]:
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


SQLALCHEMY_DATABASE_URL = _normalize_database_url(DATABASE_URL)
IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_connection():
    """Backward-compatible raw connection for legacy callers."""
    with engine.begin() as conn:
        yield conn


# =========================
# SQLITE COMPAT MIGRATIONS
# =========================
def _run_sqlite_compat_migrations() -> None:
    if not IS_SQLITE:
        return

    with engine.begin() as conn:
        cols = [
            row[1]
            for row in conn.execute(text("PRAGMA table_info(leadership_assessments)"))
        ]
        if cols and "version" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE leadership_assessments "
                    "ADD COLUMN version TEXT NOT NULL DEFAULT 'v1'"
                )
            )

        sqlite_compat_columns = {
            "account_id": "TEXT",
            "parent_id": "TEXT",
            "child_id": "TEXT",
            "submission_id": "TEXT NOT NULL DEFAULT ''",
        }
        for column, column_type in sqlite_compat_columns.items():
            if cols and column not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE leadership_assessments "
                        f"ADD COLUMN {column} {column_type}"
                    )
                )

        audiobook_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(audiobooks)"))]
        audiobook_compat_columns = {
            "source_text": "TEXT NOT NULL DEFAULT ''",
            "description": "TEXT NOT NULL DEFAULT ''",
            "cover_image_path": "TEXT NOT NULL DEFAULT '/book-covers/library-placeholder.svg'",
            "access_level": "TEXT NOT NULL DEFAULT 'free'",
            "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in audiobook_compat_columns.items():
            if audiobook_cols and column not in audiobook_cols:
                conn.execute(text(f"ALTER TABLE audiobooks ADD COLUMN {column} {column_type}"))

        progress_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(audiobook_progress)"))]
        if progress_cols and "completed_chapters" not in progress_cols:
            conn.execute(text("ALTER TABLE audiobook_progress ADD COLUMN completed_chapters TEXT NOT NULL DEFAULT '[]'"))

        subscription_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(subscriptions)"))]
        subscription_compat_columns = {
            "user_id": "INTEGER",
            "stripe_customer_id": "TEXT",
            "stripe_subscription_id": "TEXT",
            "stripe_price_id": "TEXT",
            "tier": "TEXT NOT NULL DEFAULT 'community_member'",
            "status": "TEXT NOT NULL DEFAULT 'pending'",
            "current_period_end": "DATETIME",
            "raw_metadata": "JSON NOT NULL DEFAULT '{}'",
            "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in subscription_compat_columns.items():
            if subscription_cols and column not in subscription_cols:
                conn.execute(text(f"ALTER TABLE subscriptions ADD COLUMN {column} {column_type}"))

        webhook_event_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(stripe_webhook_events)"))]
        if not webhook_event_cols:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS stripe_webhook_events ("
                "id INTEGER PRIMARY KEY, "
                "stripe_event_id TEXT NOT NULL UNIQUE, "
                "event_type TEXT NOT NULL, "
                "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            ))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stripe_webhook_events_stripe_event_id ON stripe_webhook_events (stripe_event_id)"))

        mutual_aid_request_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(mutual_aid_requests)"))]
        mutual_aid_request_columns = {
            "urgency": "TEXT NOT NULL DEFAULT 'standard'",
            "preferred_support_method": "TEXT NOT NULL DEFAULT 'community_follow_up'",
            "policy_consent": "BOOLEAN NOT NULL DEFAULT 0",
            "submitted_at": "DATETIME",
        }
        for column, column_type in mutual_aid_request_columns.items():
            if mutual_aid_request_cols and column not in mutual_aid_request_cols:
                conn.execute(text(f"ALTER TABLE mutual_aid_requests ADD COLUMN {column} {column_type}"))

        mutual_aid_document_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(mutual_aid_request_documents)"))]
        mutual_aid_document_columns = {
            "filename": "TEXT NOT NULL DEFAULT ''",
            "content_type": "TEXT NOT NULL DEFAULT ''",
            "file_size": "INTEGER NOT NULL DEFAULT 0",
        }
        for column, column_type in mutual_aid_document_columns.items():
            if mutual_aid_document_cols and column not in mutual_aid_document_cols:
                conn.execute(text(f"ALTER TABLE mutual_aid_request_documents ADD COLUMN {column} {column_type}"))

        mutual_aid_appeal_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(mutual_aid_appeals)"))]
        mutual_aid_appeal_columns = {
            "decision_id": "INTEGER",
            "explanation": "TEXT NOT NULL DEFAULT ''",
            "reviewed_by_user_id": "INTEGER",
            "review_notes": "TEXT NOT NULL DEFAULT ''",
            "reviewed_at": "DATETIME",
            "closed_at": "DATETIME",
            "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in mutual_aid_appeal_columns.items():
            if mutual_aid_appeal_cols and column not in mutual_aid_appeal_cols:
                conn.execute(text(f"ALTER TABLE mutual_aid_appeals ADD COLUMN {column} {column_type}"))

        audio_asset_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(audio_assets)"))]
        audio_asset_compat_columns = {
            "audiobook_id": "INTEGER",
            "chapter_id": "INTEGER",
            "title": "TEXT",
            "model": "TEXT",
            "duration_seconds": "INTEGER",
            "format": "TEXT NOT NULL DEFAULT 'mp3'",
            "storage_key": "TEXT",
            "filename": "TEXT",
        }
        for column, column_type in audio_asset_compat_columns.items():
            if audio_asset_cols and column not in audio_asset_cols:
                conn.execute(text(f"ALTER TABLE audio_assets ADD COLUMN {column} {column_type}"))


# =========================
# DATABASE TYPE DETECTION
# =========================
def get_database_type() -> str:
    if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        return "postgres"
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return "sqlite"
    return "unknown"


def is_unsafe_sqlite_fallback() -> bool:
    return IS_SQLITE and not os.getenv("DATABASE_URL")


def enforce_database_url_for_production() -> None:
    if not is_production_like_environment():
        return
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required in production-like environments.")
    if IS_SQLITE:
        raise RuntimeError("Production-like environments must use a persistent Postgres DATABASE_URL, not SQLite.")


# =========================
# SQLITE PATH HELPER
# =========================
def _sqlite_db_path() -> str | None:
    if not IS_SQLITE:
        return None
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
        return SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "", 1)
    return None


# =========================
# DEV RESET (SAFE-GUARDED)
# =========================
def reset_local_sqlite_database() -> dict:
    """
    Destructive dev-only reset for local SQLite databases.
    NEVER runs on Postgres.
    """
    if not IS_SQLITE:
        return {"ok": False, "reason": "Database is not SQLite; reset skipped."}

    db_path = _sqlite_db_path()
    if not db_path or db_path in {":memory:", ""}:
        return {"ok": False, "reason": "SQLite path is not a local file; reset skipped."}

    try:
        if os.path.exists(db_path):
            os.remove(db_path)

        # Recreate schema
        from app import models  # noqa: F401

        Base.metadata.create_all(bind=engine)

        return {
            "ok": True,
            "database": db_path,
            "message": "SQLite database reset complete.",
        }

    except Exception as exc:
        return {"ok": False, "reason": str(exc)}


# =========================
# LIGHTWEIGHT COMPAT MIGRATIONS
# =========================
def _run_generic_compat_migrations() -> None:
    if IS_SQLITE:
        return

    with engine.begin() as conn:
        dialect = engine.dialect.name
        if dialect != "postgresql":
            return

        subscription_columns = {
            "user_id": "INTEGER",
            "stripe_customer_id": "TEXT",
            "stripe_subscription_id": "TEXT",
            "stripe_price_id": "TEXT",
            "tier": "TEXT NOT NULL DEFAULT 'community_member'",
            "status": "TEXT NOT NULL DEFAULT 'pending'",
            "current_period_end": "TIMESTAMP",
            "raw_metadata": "JSONB NOT NULL DEFAULT '{}'::jsonb",
            "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in subscription_columns.items():
            conn.execute(text(f"ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS {column} {column_type}"))

        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS stripe_webhook_events ("
            "id SERIAL PRIMARY KEY, "
            "stripe_event_id TEXT NOT NULL UNIQUE, "
            "event_type TEXT NOT NULL, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ")"
        ))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stripe_webhook_events_stripe_event_id ON stripe_webhook_events (stripe_event_id)"))

        audiobook_columns = {
            "source_text": "TEXT NOT NULL DEFAULT ''",
            "description": "TEXT NOT NULL DEFAULT ''",
            "cover_image_path": "TEXT NOT NULL DEFAULT '/book-covers/library-placeholder.svg'",
            "access_level": "TEXT NOT NULL DEFAULT 'free'",
            "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in audiobook_columns.items():
            conn.execute(text(f"ALTER TABLE audiobooks ADD COLUMN IF NOT EXISTS {column} {column_type}"))

        conn.execute(text("ALTER TABLE audiobook_progress ADD COLUMN IF NOT EXISTS completed_chapters TEXT NOT NULL DEFAULT '[]'"))

        mutual_aid_request_columns = {
            "urgency": "TEXT NOT NULL DEFAULT 'standard'",
            "preferred_support_method": "TEXT NOT NULL DEFAULT 'community_follow_up'",
            "policy_consent": "BOOLEAN NOT NULL DEFAULT false",
            "submitted_at": "TIMESTAMP",
        }
        for column, column_type in mutual_aid_request_columns.items():
            conn.execute(text(f"ALTER TABLE mutual_aid_requests ADD COLUMN IF NOT EXISTS {column} {column_type}"))

        mutual_aid_document_columns = {
            "filename": "TEXT NOT NULL DEFAULT ''",
            "content_type": "TEXT NOT NULL DEFAULT ''",
            "file_size": "INTEGER NOT NULL DEFAULT 0",
        }
        for column, column_type in mutual_aid_document_columns.items():
            conn.execute(text(f"ALTER TABLE mutual_aid_request_documents ADD COLUMN IF NOT EXISTS {column} {column_type}"))

        mutual_aid_appeal_columns = {
            "decision_id": "INTEGER",
            "explanation": "TEXT NOT NULL DEFAULT ''",
            "reviewed_by_user_id": "INTEGER",
            "review_notes": "TEXT NOT NULL DEFAULT ''",
            "reviewed_at": "TIMESTAMP",
            "closed_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column, column_type in mutual_aid_appeal_columns.items():
            conn.execute(text(f"ALTER TABLE mutual_aid_appeals ADD COLUMN IF NOT EXISTS {column} {column_type}"))

        audio_asset_columns = {
            "audiobook_id": "INTEGER",
            "chapter_id": "INTEGER",
            "title": "TEXT",
            "model": "TEXT",
            "duration_seconds": "INTEGER",
            "format": "TEXT NOT NULL DEFAULT 'mp3'",
            "storage_key": "TEXT",
            "filename": "TEXT",
        }
        for column, column_type in audio_asset_columns.items():
            conn.execute(text(f"ALTER TABLE audio_assets ADD COLUMN IF NOT EXISTS {column} {column_type}"))


# =========================
# MUTUAL AID COMPAT MIGRATIONS
# =========================
def _ensure_mutual_aid_fund_phase5_columns() -> None:
    """Ensure older mutual_aid_funds tables have Phase 5 control columns.

    SQLAlchemy selects every mapped MutualAidFund column when seeding the
    default fund. Existing production databases may already have the table from
    an earlier migration, and create_all() will not add newly mapped columns to
    that table. Keep this defensive check before any MutualAidFund ORM query.
    """
    phase5_columns = {
        "reserve_percent": "INTEGER NOT NULL DEFAULT 10",
        "approval_threshold": "INTEGER NOT NULL DEFAULT 500",
    }

    with engine.begin() as conn:
        dialect = engine.dialect.name
        if dialect == "postgresql":
            for column, column_type in phase5_columns.items():
                conn.execute(
                    text(
                        "ALTER TABLE mutual_aid_funds "
                        f"ADD COLUMN IF NOT EXISTS {column} {column_type}"
                    )
                )
            return

        if dialect == "sqlite":
            existing_columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(mutual_aid_funds)"))
            }
            if not existing_columns:
                return
            for column, column_type in phase5_columns.items():
                if column not in existing_columns:
                    conn.execute(
                        text(
                            "ALTER TABLE mutual_aid_funds "
                            f"ADD COLUMN {column} {column_type}"
                        )
                    )

# =========================
# INIT DB (UNIFIED VERSION)
# =========================
def init_db() -> None:
    """
    Initializes DB + runs compatibility migrations.
    Safe for both SQLite and Postgres.
    """
    from app import models  # ensures models are registered

    Base.metadata.create_all(bind=engine)
    _run_sqlite_compat_migrations()
    _run_generic_compat_migrations()
    _ensure_mutual_aid_fund_phase5_columns()

    db = SessionLocal()
    try:
        from app.services.mutual_aid import seed_default_mutual_aid_fund
        from app.services.society_builder import seed_simba_main_hub

        seed_default_mutual_aid_fund(db)
        seed_simba_main_hub(db)
    finally:
        db.close()
