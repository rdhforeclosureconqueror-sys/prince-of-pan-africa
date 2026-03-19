from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me")
def auth_me(db: Session = Depends(get_db)):
    user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        return {
            "ok": True,
            "auth": False,
            "authenticated": False,
            "user": None,
        }

    return {
        "ok": True,
        "auth": True,
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }