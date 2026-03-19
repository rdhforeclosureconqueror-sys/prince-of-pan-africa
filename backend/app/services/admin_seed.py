from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ActivityLog, MemberProfile, User
from app.security import hash_password

ADMIN_EMAIL = "rdhforeclosureconqueror@gmail.com"
ADMIN_PASSWORD = "beastmode"
ADMIN_ROLE = "admin"


def _ensure_profile_and_activity(db: Session, user: User) -> None:
    if not user.profile:
        db.add(
            MemberProfile(
                user_id=user.id,
                role=user.role,
                attributes={"level": "founder", "status": "active"},
            )
        )

    has_seed_activity = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id, ActivityLog.action == "admin_seeded")
        .first()
    )
    if not has_seed_activity:
        db.add(ActivityLog(user_id=user.id, action="admin_seeded"))


def seed_admin() -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not user:
            user = User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role=ADMIN_ROLE,
            )
            db.add(user)
            db.flush()
            created = True
        else:
            created = False

        _ensure_profile_and_activity(db, user)
        db.commit()
        return {"created": created, "email": user.email, "role": user.role, "user_id": user.id}
    finally:
        db.close()
