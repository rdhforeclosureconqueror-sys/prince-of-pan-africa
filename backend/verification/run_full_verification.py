#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full backend verification checks.")
    parser.add_argument(
        "--reset-sqlite",
        action="store_true",
        help="DEV-ONLY: Destructively reset local SQLite database before verification.",
    )
    args = parser.parse_args()

    try:
        from app.database import get_database_type, init_db, reset_local_sqlite_database
        from app.main import app
        from app.services.admin_seed import seed_admin
        from verification.verification_engine import build_full_system_verification
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Dependency import failed",
                    "details": str(exc),
                    "hint": "Install backend requirements before running verification.",
                },
                indent=2,
            )
        )
        return 1

    if args.reset_sqlite:
        reset_result = reset_local_sqlite_database()
        print(json.dumps({"sqlite_reset": reset_result}, indent=2))
        if not reset_result.get("ok"):
            print("SQLite reset failed or skipped.")

    init_db()
    seed_admin()

    report = build_full_system_verification(app)
    report["database_type"] = get_database_type()
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
