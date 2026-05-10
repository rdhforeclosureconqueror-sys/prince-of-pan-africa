#!/usr/bin/env python3
"""Audit and optionally grant subscriber access for known paid users.

This script intentionally does not try to infer paid status from application data,
because this codebase does not currently store billing/subscription records. Feed it
an authoritative paid-customer export from the payment system with `--paid-users-csv`
or pass one or more `--paid-user-email` values.

Dry run audit example:
    PYTHONPATH=backend DATABASE_URL=... python backend/scripts/paid_subscriber_access.py \
        --paid-users-csv paid_users.csv

Apply by adding a subscriber row in `user_roles` after reviewing the dry run:
    PYTHONPATH=backend DATABASE_URL=... python backend/scripts/paid_subscriber_access.py \
        --paid-users-csv paid_users.csv \
        --apply \
        --confirm ASSIGN_SUBSCRIBER
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

PAID_ACCESS_ROLE_NAMES = {"subscriber", "admin", "superadmin"}
SUBSCRIBER_ROLE_NAME = "subscriber"
CONFIRMATION_TEXT = "ASSIGN_SUBSCRIBER"


@dataclass(frozen=True)
class PaidUserAuditRow:
    email: str
    user_id: int | None
    users_role: str | None
    user_roles: tuple[str, ...]
    status: str
    has_paid_access: bool
    needs_subscriber_access: bool


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def load_paid_user_emails(csv_path: str | None, explicit_emails: list[str]) -> list[str]:
    emails: list[str] = []

    if csv_path:
        with open(csv_path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("Paid-user CSV must include a header row with an email column.")

            email_column = next(
                (column for column in reader.fieldnames if column and column.strip().lower() == "email"),
                None,
            )
            if not email_column:
                raise ValueError("Paid-user CSV must include an `email` column.")

            for row in reader:
                emails.append(normalize_email(row.get(email_column, "")))

    emails.extend(normalize_email(email) for email in explicit_emails)

    seen: set[str] = set()
    unique_emails: list[str] = []
    for email in emails:
        if not email or email in seen:
            continue
        seen.add(email)
        unique_emails.append(email)
    return unique_emails


def effective_role_names(users_role: str | None, user_roles: tuple[str, ...]) -> set[str]:
    role_names = {role.strip().lower() for role in user_roles if role and role.strip()}
    if not role_names and users_role:
        role_names.add(users_role.strip().lower())
    return role_names


def build_audit_row(email: str, user) -> PaidUserAuditRow:
    if user is None:
        return PaidUserAuditRow(
            email=email,
            user_id=None,
            users_role=None,
            user_roles=(),
            status="missing_user",
            has_paid_access=False,
            needs_subscriber_access=True,
        )

    user_role_names = tuple(sorted({user_role.role.name for user_role in user.user_roles if user_role.role}))
    role_names = effective_role_names(user.role, user_role_names)
    has_paid_access = bool(role_names & PAID_ACCESS_ROLE_NAMES)
    has_explicit_subscriber = user.role == SUBSCRIBER_ROLE_NAME or SUBSCRIBER_ROLE_NAME in user_role_names
    status = "ok" if has_paid_access else "missing_subscriber_access"

    return PaidUserAuditRow(
        email=email,
        user_id=user.id,
        users_role=user.role,
        user_roles=user_role_names,
        status=status,
        has_paid_access=has_paid_access,
        needs_subscriber_access=not has_paid_access or not has_explicit_subscriber,
    )


def audit_paid_users(db, paid_emails: list[str]) -> list[PaidUserAuditRow]:
    from app.models import User

    rows: list[PaidUserAuditRow] = []
    for email in paid_emails:
        user = db.query(User).filter(User.email == email).first()
        rows.append(build_audit_row(email, user))
    return rows


def ensure_subscriber_user_role(db, user_id: int) -> bool:
    from app.models import Role, UserRole

    subscriber_role = db.query(Role).filter(Role.name == SUBSCRIBER_ROLE_NAME).first()
    if subscriber_role is None:
        raise RuntimeError("Subscriber role is missing after RBAC seeding.")

    existing = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.role_id == subscriber_role.id)
        .first()
    )
    if existing:
        return False

    db.add(UserRole(user_id=user_id, role_id=subscriber_role.id))
    return True


def set_users_role_to_subscriber(db, user_id: int) -> bool:
    from app.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False
    if user.role == SUBSCRIBER_ROLE_NAME:
        return False
    user.role = SUBSCRIBER_ROLE_NAME
    return True


def apply_subscriber_access(db, rows: list[PaidUserAuditRow], assignment_mode: str) -> int:
    changed_count = 0
    for row in rows:
        if row.user_id is None or not row.needs_subscriber_access:
            continue
        if assignment_mode == "users-role":
            changed = set_users_role_to_subscriber(db, row.user_id)
        else:
            changed = ensure_subscriber_user_role(db, row.user_id)
        if changed:
            changed_count += 1
    db.commit()
    return changed_count


def print_audit_table(rows: list[PaidUserAuditRow]) -> None:
    header = ["email", "user_id", "users.role", "user_roles", "status"]
    print("\t".join(header))
    for row in rows:
        print(
            "\t".join(
                [
                    row.email,
                    str(row.user_id or ""),
                    row.users_role or "",
                    ",".join(row.user_roles) or "",
                    row.status,
                ]
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit known paid users and optionally grant subscriber access."
    )
    parser.add_argument(
        "--paid-users-csv",
        help="Path to a payment-system export with an `email` header column.",
    )
    parser.add_argument(
        "--paid-user-email",
        action="append",
        default=[],
        help="Paid user email to audit. May be passed multiple times.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply subscriber access changes. Default is audit-only dry run.",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Required with --apply. Must equal {CONFIRMATION_TEXT!r}.",
    )
    parser.add_argument(
        "--assignment-mode",
        choices=["user-roles", "users-role"],
        default="user-roles",
        help="How to grant access when applying. Default adds a user_roles subscriber row.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paid_emails = load_paid_user_emails(args.paid_users_csv, args.paid_user_email)
    if not paid_emails:
        print("No paid users supplied. Provide --paid-users-csv or --paid-user-email.", file=sys.stderr)
        return 2

    if args.apply and args.confirm != CONFIRMATION_TEXT:
        print(
            f"Refusing to apply changes without --confirm {CONFIRMATION_TEXT}.",
            file=sys.stderr,
        )
        return 2

    from app.authz import seed_rbac_defaults
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_rbac_defaults(db)
        rows = audit_paid_users(db, paid_emails)
        print_audit_table(rows)

        missing_users = [row for row in rows if row.status == "missing_user"]
        missing_access = [row for row in rows if row.status == "missing_subscriber_access"]
        needs_assignment = [row for row in rows if row.user_id is not None and row.needs_subscriber_access]

        print()
        print(f"Paid users supplied: {len(rows)}")
        print(f"Missing application users: {len(missing_users)}")
        print(f"Paid users without paid-access roles: {len(missing_access)}")
        print(f"Existing users needing subscriber assignment: {len(needs_assignment)}")

        if not args.apply:
            print("Dry run only. Re-run with --apply --confirm ASSIGN_SUBSCRIBER to assign access.")
            return 1 if missing_users or missing_access else 0

        changed_count = apply_subscriber_access(db, rows, args.assignment_mode)
        print(f"Subscriber assignments applied: {changed_count}")
        if missing_users:
            print("Some paid emails do not match application users; no assignment was possible for them.")
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
