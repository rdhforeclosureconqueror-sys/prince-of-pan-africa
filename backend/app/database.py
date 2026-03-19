import os
import sqlite3
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mufasa.db")


def _resolve_sqlite_path() -> str:
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "", 1)
    return "mufasa.db"


DB_PATH = _resolve_sqlite_path()


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leadership_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                responses TEXT NOT NULL,
                scores TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT 'v1',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Lightweight migration for existing databases created before version column.
        cols = [row[1] for row in conn.execute("PRAGMA table_info(leadership_assessments)").fetchall()]
        if "version" not in cols:
            conn.execute("ALTER TABLE leadership_assessments ADD COLUMN version TEXT NOT NULL DEFAULT 'v1'")

        conn.commit()
