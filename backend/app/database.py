import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mufasa.db")


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


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_sqlite_compat_migrations()
