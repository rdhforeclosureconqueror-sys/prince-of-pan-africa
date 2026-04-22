import os

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ActivityLog, MemberProfile, User
from app.security import hash_password


DEFAULT_SUPERADMIN_EMAIL = "rdhforeclosurconqueror@gmail.com"
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", DEFAULT_SUPERADMIN_EMAIL).strip().lower()
ADMIN_EMAIL = SUPERADMIN_EMAIL  # backward compatibility for verification checks
SUPERADMIN_ROLE = "superadmin"


def _find_users_by_normalized_email(db: Session, normalized_email: str) -> list[User]:
    return (
        db.query(User)
        .filter(func.lower(func.trim(User.email)) == normalized_email)
        .order_by(User.id.asc())
        .all()
    )


def _ensure_profile_and_activity(db: Session, user: User) -> None:
    profile = user.profile
    if not profile:
        profile = MemberProfile(
            user_id=user.id,
            role=user.role,
            attributes={"level": "founder", "status": "active"},
        )
        db.add(profile)
    elif profile.role != user.role:
        profile.role = user.role

    has_seed_activity = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id, ActivityLog.action == "superadmin_seeded")
        .first()
    )
    if not has_seed_activity:
        db.add(ActivityLog(user_id=user.id, action="superadmin_seeded"))


def _resolve_password_hash() -> str | None:
    seed_password_hash = os.getenv("SUPERADMIN_PASSWORD_HASH", "").strip()
    if seed_password_hash:
        return seed_password_hash

    seed_password_plaintext = os.getenv("SUPERADMIN_PASSWORD", "")
    if seed_password_plaintext:
        return hash_password(seed_password_plaintext)

    return None


def seed_admin() -> dict:
    """
    Ensure the configured superadmin user exists with role=superadmin and canonical email.
    - Existing users are role-upgraded and can have password_hash synchronized when
      SUPERADMIN_PASSWORD_HASH or SUPERADMIN_PASSWORD is provided.
    - New users are only created when SUPERADMIN_PASSWORD_HASH or
      SUPERADMIN_PASSWORD is provided at runtime.
    """
    db = SessionLocal()
    try:
        password_hash = _resolve_password_hash()
        matches = _find_users_by_normalized_email(db, SUPERADMIN_EMAIL)
        duplicate_user_ids = [user.id for user in matches[1:]] if len(matches) > 1 else []

        if not matches:
            if not password_hash:
                return {
                    "created": False,
                    "updated": False,
                    "email": SUPERADMIN_EMAIL,
                    "role": SUPERADMIN_ROLE,
                    "skipped": True,
                    "reason": "missing SUPERADMIN_PASSWORD_HASH or SUPERADMIN_PASSWORD",
                    "duplicates_detected": False,
                    "duplicate_user_ids": [],
                }
            user = User(
                email=SUPERADMIN_EMAIL,
                password_hash=password_hash,
                role=SUPERADMIN_ROLE,
            )
            db.add(user)
            db.flush()
            created = True
            updated = False
        else:
            user = matches[0]
            created = False
            updated = False

            if user.email != SUPERADMIN_EMAIL:
                user.email = SUPERADMIN_EMAIL
                updated = True

            if user.role != SUPERADMIN_ROLE:
                user.role = SUPERADMIN_ROLE
                updated = True

            if password_hash and user.password_hash != password_hash:
                user.password_hash = password_hash
                updated = True

        _ensure_profile_and_activity(db, user)
        db.commit()

        return {
            "created": created,
            "updated": updated,
            "email": user.email,
            "role": user.role,
            "user_id": user.id,
            "skipped": False,
            "duplicates_detected": bool(duplicate_user_ids),
            "duplicate_user_ids": duplicate_user_ids,
            "password_from_env": bool(password_hash),
        }
    finally:
        db.close()
