import os

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ActivityLog, MemberProfile, User
from app.security import hash_password

SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "rdhforeclosurconqueror@gmail.com").strip().lower()
ADMIN_EMAIL = SUPERADMIN_EMAIL  # backward compatibility for verification checks
SUPERADMIN_ROLE = "superadmin"


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
    Ensure the configured superadmin user exists with role=superadmin.
    - Existing users are role-upgraded without changing password_hash.
    - New users are only created when SUPERADMIN_PASSWORD_HASH or
      SUPERADMIN_PASSWORD is provided at runtime.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
        password_hash = _resolve_password_hash()

        if not user:
            if not password_hash:
                return {
                    "created": False,
                    "updated": False,
                    "email": SUPERADMIN_EMAIL,
                    "role": SUPERADMIN_ROLE,
                    "skipped": True,
                    "reason": "missing SUPERADMIN_PASSWORD_HASH or SUPERADMIN_PASSWORD",
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
            created = False
            updated = False
            if user.role != SUPERADMIN_ROLE:
                user.role = SUPERADMIN_ROLE
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
        }
    finally:
        db.close()
